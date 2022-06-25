import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';
import {
  INotebookTracker, NotebookActions, NotebookPanel,
} from '@jupyterlab/notebook';
import {getFirstVisibleNotebookPanel, showError} from './utils';
import {IDocumentManager} from '@jupyterlab/docmanager';
import {ButtonExtension} from './toolbarButtonExtension';
import {Session} from "./session";
import {getShouldSaveLoadWithinNotebook, setShouldSaveLoadWithinNotebook} from "./globalConfig";
import {getShowWithinNotebook, setShowWithinNotebook} from "./globalConfig";


/**
 * Initialization data for the extension quibbler.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'quibbler:plugin',
  autoStart: true,
  requires: [INotebookTracker, IDocumentManager],
  activate: (
    app: JupyterFrontEnd,
    notebooks: INotebookTracker,
    documentManager: IDocumentManager,
  ) => {
    console.log("Starting quibbler plugin...");

    const {commands} = app;
    const kernelIdsToSessions = new Map();

    const undoButton = new ButtonExtension('Undo', () => runActionOnCurrentSession('undo', {}));
    const redoButton = new ButtonExtension('Redo', () => runActionOnCurrentSession('redo', {}));
    app.docRegistry.addWidgetExtension('Notebook', redoButton);
    app.docRegistry.addWidgetExtension('Notebook', undoButton);
    
    const getCurrentNotebookPanel = () => {
      return getFirstVisibleNotebookPanel(app);
    }

    NotebookActions.executed.connect((_, {cell, success, notebook}) => {
      // @ts-ignore
      const session = getOrRegisterSession(getCurrentNotebookPanel());
      session.handleCellExecution(cell);
    });


    const handleRemoteQuibsArchiveChange = (panel: any, data: any) => {
      // @ts-ignore
      panel.content.model.metadata.set("quibs_archive", data);

      documentManager.contextForWidget(panel)?.save();
    }

    const getOrRegisterSession = (panel: NotebookPanel) => {
      const kernel = panel.sessionContext.session?.kernel;

      // @ts-ignore FOR TEST ENV
      Window.pyquibblerKernel = panel.sessionContext.session?.kernel;

      if (kernel === null || kernel === undefined) {
        throw new Error("No kernel exists for panel");
      }

      if (!kernelIdsToSessions.has(kernel.id)) {
        kernelIdsToSessions.set(kernel.id, Session(panel, kernel, handleRemoteQuibsArchiveChange));
      }

      return kernelIdsToSessions.get(kernel.id);
    }


    /**
     * Run an action (eg "undo") on the currently session. This can potentially create a comm if necessary, and will
     * handle situations in which there is no running pyquibbler
     *
     * @param action - to run on pyquiibbler
     * @param parameters - to send to pyquibbler
     * @param shouldShowError - should show error on failure?
     */
    const runActionOnCurrentSession = async (action: string, parameters: any, shouldShowError?: boolean) => {
      console.log("Running", action);
      shouldShowError = shouldShowError !== false;
      let session;
      try {
        // @ts-ignore
        session = getOrRegisterSession(getCurrentNotebookPanel())
      } catch (error) {
        if (shouldShowError) {
          showError(error);
          return;
        } else {
          throw error;
        }
      }

      try {
        await session.runAction(action, parameters);
      } catch (error) {
        if (shouldShowError) {
          showError(error);
          return;
        } else {
          throw error;
        }
      }
    }

    const fileSavingCommands = [
      {
        command: 'save',
        label: 'Save Quibs',
        action: 'save'
      },
      {
        command: 'load',
        label: 'Load Quibs',
        action: 'load'
      },
      {
        command: 'sync',
        label: 'Sync Quibs',
        action: 'sync',
      },
    ]

    fileSavingCommands.map(({command, action, label}) => {
      // Add a command
      commands.addCommand(`quibbler:${command}`, {
        label: label,
        execute: (args: any) => {
          const panel = getFirstVisibleNotebookPanel(app);
          if (panel == null) {
            showError("There is no open notebook!");
            return;
          }

          documentManager.contextForWidget(panel)?.save().then(() => {
            runActionOnCurrentSession(action, {});
          });
        }
      });
    });

    commands.addCommand('quibbler:save-in-notebook', {
      label: 'Save/Load inside Notebook',
      execute: (args: any) => {
        setShouldSaveLoadWithinNotebook(!getShouldSaveLoadWithinNotebook())
        for (let session of kernelIdsToSessions.values()) {
          session.runAction("setShouldSaveLoadWithinNotebook", {
            should_save_load_within_notebook: getShouldSaveLoadWithinNotebook()
          });
        }
      },
      isToggled: () => getShouldSaveLoadWithinNotebook()
    });

    commands.addCommand('quibbler:clear-data', {
      label: "Clear Quib Data in Notebook",
      execute: (args: any) => {
        const panel = getFirstVisibleNotebookPanel(app);
        if (panel == null) {
          showError("There is no open notebook!");
          return;
        }

        handleRemoteQuibsArchiveChange(panel, null);

        documentManager.contextForWidget(panel)?.save().then(() => {
          runActionOnCurrentSession("clearData", {}, false).catch((e) => {
            console.log(`Not sending clear data to server, because of error ${e}`)
          });
        })
      }
    });

    commands.addCommand('quibbler:show-quibs', {
      label: 'Show Quibs under Notebook cells',
      execute: (args: any) => {
        setShowWithinNotebook(!getShowWithinNotebook())
      },
      isToggled: () => getShowWithinNotebook()
    });

    notebooks.widgetAdded.connect((sender: any, nbPanel: NotebookPanel) => {
      nbPanel.sessionContext.ready.then(() => {
        console.log("Session context ready- preparing session...");
        getOrRegisterSession(nbPanel);
      });
      nbPanel.sessionContext.sessionChanged.connect((e, f) => {
        e.kernelChanged.connect((k, changedKernel) => {
          if (changedKernel.newValue === null) {
            kernelIdsToSessions.delete(changedKernel.oldValue!.id);
          }
        })
      })
    });
  }
};

export default plugin;
