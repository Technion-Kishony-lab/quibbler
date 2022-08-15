import { DocumentRegistry } from '@jupyterlab/docregistry';
import { INotebookModel, NotebookPanel } from '@jupyterlab/notebook';
import { IDisposable } from '@lumino/disposable';
import { ToolbarButton } from '@jupyterlab/apputils';

export class ButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {

  private readonly label: string;
  private readonly callback: () => void;
  button: ToolbarButton

  constructor(label: string, callback: () => void) {
    this.label = label;
    this.callback = callback;
    this.button = new ToolbarButton();
  }

  createNew(panel: NotebookPanel): IDisposable {
    const button = new ToolbarButton({
      label: this.label,
      onClick: this.callback
    });

    panel.toolbar.insertItem(10, this.label, button);
    button.enabled = false
    this.button = button
    return button;
  }
}
