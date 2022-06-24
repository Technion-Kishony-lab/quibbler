import Swal from 'sweetalert2';
import {JupyterFrontEnd} from '@jupyterlab/application';
import axios from 'axios';


export const showDialog = (options: any) => {
  Swal.fire(options);
}


export const showRequestDialog = async (title: string, text: string, options: {[id: string]: string}, port: number) => {

  let optionsString = '';
  Object.keys(options).forEach(option => {
    optionsString += option + ': ' + options[option] + '\n';
  });

  // @ts-ignore
  const { value } = await Swal.fire({
    title: title,
    input: 'text',
    inputLabel: `${text}\n${optionsString}`,
    inputValue: options,
    showCancelButton: false,
    icon: "warning",
    inputPlaceholder: "Choose a number (e.g. 1) from the options",
    allowOutsideClick: false,
    inputValidator: (value) => {
      if (!(value in options)) {
        return 'You must choose from the given options'
      }
    }
  })

  await axios.post(`http://localhost:${port}/answer`, {
    option: value
  })

}

export const showError = (reason: any) => {
  Swal.fire({
    icon: 'error',
    title: 'Oops...',
    text: reason,
  });
}


export const getFirstVisibleNotebookPanel = (app: JupyterFrontEnd) => {
  const mainWidgets = app.shell.widgets('main');
  let widget = mainWidgets.next();
  while (widget) {
    // @ts-ignore
    if (widget.sessionContext) {
      // @ts-ignore
      const type = widget.sessionContext.type;
      if (type === 'notebook') {
        if (widget.isVisible) {
          return widget;
        }
      }
    }
    widget = mainWidgets.next();
  }

  return null;
};


export const showErrorOnFailure = async (promise: Promise<any>) => {
  try {
    return await promise;
  } catch (e) {
    showError(e as string);
    throw e;
  }
}