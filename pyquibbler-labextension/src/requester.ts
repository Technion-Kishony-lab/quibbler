import {IComm} from "@jupyterlab/services/lib/kernel/kernel";
import { v4 as uuidv4 } from 'uuid';

export interface IRequester {
  request: (action: string, parameters: any) => Promise<any>
  handleSuccessResponse: (requestId: string, data: any) => void,
  handleErrorResponse: (requestId: string, data: any) => void,
  cancelPendingRequests: () => void
}

/**
 * A requester is used to interact with the `JupyterProject` in it's protocol- this abstracts interactions for
 * whoever uses this into a simple request-response methodology
 */
export const Requester = (comm: IComm) => {
  const idsToPromiseResolves = new Map();
  const idsToPromiseRejects = new Map();

  const cleanup = (requestId: string) => {
    idsToPromiseResolves.delete(requestId);
    idsToPromiseRejects.delete(requestId)
  }

  return  {
    request: (action: string, parameters: any) => {
      console.log("Sending action", action);
      const uuid = uuidv4();
      return new Promise((resolve, reject) => {
        idsToPromiseResolves.set(uuid, resolve);
        idsToPromiseRejects.set(uuid, reject);

        // There's a weird bug in which if you send two things in comm right after each other, there is a potential
        // for a situation in which the second will not be sent until ANOTHER message is sent in the comm. Therefore,
        // we delay ourselves by 100ms if there's already a request
        const timeout =  (idsToPromiseResolves.size > 1) ? 100 : 0;
        setTimeout(() => {
          try {
            comm.send({action, parameters, requestId: uuid});
          } catch (error) {
            console.log("Failed with error", error);
            throw new Error(`Cannot send ${action} - is pyquibbler running? (You need to run \`initialize_quibbler\`)`)
          }
        }, timeout);
      });
    },
    handleSuccessResponse: (requestId: string, data: any) => {
      console.log("Resolving", requestId, idsToPromiseResolves);
      if (idsToPromiseResolves.has(requestId)) {
        idsToPromiseResolves.get(requestId)(data);
      }
      cleanup(requestId);
    },
    handleErrorResponse: (requestId: string, data: any) => {
      if (idsToPromiseResolves.has(requestId)) {
        idsToPromiseRejects.get(requestId)(data)
      }
      cleanup(requestId);
    },
    cancelPendingRequests: () => {
      idsToPromiseResolves.clear();
      idsToPromiseRejects.clear();
    }
  }
}
