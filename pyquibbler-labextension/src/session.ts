import {NotebookPanel} from "@jupyterlab/notebook";
import {IComm, IKernelConnection} from "@jupyterlab/services/lib/kernel/kernel";
import {showDialog, showRequestDialog} from "./utils";
import {IRequester, Requester} from "./requester";
import {ButtonExtension} from './toolbarButtonExtension';

/**
 * Represents a session between the client and a specific kernel. A session will create a requester once pyquibbler
 * is loaded (`initialize_quibbler`)
 */
export const Session = (panel: NotebookPanel,
                        kernel: IKernelConnection,
                        undoButton: ButtonExtension,
                        redoButton: ButtonExtension,
                        onRemoteQuibsArchiveChange: (panel: any, newQuibsArchive: any) => void ) => {

  let comm: IComm | null = null;
  let requester: IRequester | null = null;

  kernel.statusChanged.connect((k,
                                status) => {
    if (status === "terminating" || status === "restarting" || status === "autorestarting") {
      getRequester().request("cleanup", {})
    }
  });

  const getRequester = () => {
    if (requester == null) {
      throw new Error("Jupyter is not connected with pyquibbler.  " +
          "Run `initialize_quibbler(jupyterlab_extension=True)` to connect.");
    }
    return requester;
  }


  /**
   * For a given notebook panel, find/create a pyquibbler com
   *
   * */
  const registerComm = async () => {
    const commInfoResult = await kernel.requestCommInfo({target_name: 'pyquibbler'});

    // @ts-ignore
    const comms = commInfoResult.content.comms;
    const commId = Object.keys(comms).find((id_) => comms[id_].target_name === 'pyquibbler');

    console.log("Registering comm target for pyquibbler");
    kernel.registerCommTarget('pyquibbler',
      (c: IComm) => {
        comm = c;
        console.log('Callback: registering comm');
        saveAndSetCallbackToComm();
      }
    );

    if (commId) {
      console.log('Found existing comm id, recreating and reregistering');
      // There exists a comm, but we do not have it on client side (we probably refreshed the browser). Recreate it.
      comm = kernel!.createComm('pyquibbler', commId);
      saveAndSetCallbackToComm();
    }
  }

  /**
   * Save the comm and set the callback on it whenever receiving a message- this will simply show an error to the
   * user
   *
   */
  const saveAndSetCallbackToComm = () => {
    if (comm === null) {
      throw new Error("No comm available yet!");
    }

    requester = Requester(comm);

    comm.onMsg = ((msg) => {
      const pyquibblerMessage = msg.content.data;
      console.log("Received message", pyquibblerMessage);
      const msgType = pyquibblerMessage.type;
      const data: any = pyquibblerMessage.data!;
      switch (msgType) {
        case 'dialog':
          showDialog(data);
          break;
        case 'requestDialog': {
          showRequestDialog(data.title, data.message, data.options, data.port);
          break;
        }
        case 'quibsArchiveUpdate': {
          onRemoteQuibsArchiveChange(panel, data);
          break;
        }
        case 'setUndoRedoButtons': {
          undoButton.button.enabled = data.undoEnabled == 'True';
          redoButton.button.enabled = data.redoEnabled == 'True';
          break;
        }
        case "response": {
          getRequester().handleSuccessResponse(pyquibblerMessage.requestId as string, data);
          break;
        }
        case "error": {
          getRequester().handleErrorResponse(pyquibblerMessage.requestId as string, data);
          break;
        }
      }
      return new Promise((resolve) => resolve());
    }
    );
  }

  registerComm();

  return {
    runAction: (action: string, parameters: any) => {
      return getRequester().request(action, parameters)
    },
  }
}