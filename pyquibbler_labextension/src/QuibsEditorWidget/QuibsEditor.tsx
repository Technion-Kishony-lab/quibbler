import { ReactWidget } from '@jupyterlab/apputils';
import React, { useState } from 'react';
import styled from "styled-components";
import {IRequester} from "../requester";
import {Quib} from "./types";
import {QuibEditor} from "./QuibEditor";
import { Signal } from '@lumino/signaling';
import { UseSignal } from '@jupyterlab/apputils';

const QuibTab = styled.div`
  display: flex;
  background-color: ${props => props.className === "active" ? "white" : "rgb(238, 238, 238)"};
  padding: 4px;
  border-style: solid;
  border-width: 0 1px 2px 0px;
  border-color:  ${props => props.className === "active" ? "rgb(56, 116, 203) rgb(190, 189, 189)" : "rgb(190, 189, 189)"};
  
  &:hover {
    background-color: white;
  }
`

const QuibsEditor = (props: {
  signal: Signal<any, Quib[]>,
  initialQuibs: Quib[],
  onChangeQuib: (quib: Quib) => void,
  requester: IRequester }) => {

  const [selectedQuibNames, setSelectedQuibNames] = useState<string[]>([]);

  const quibInSelectedQuibs = (quib: Quib) => selectedQuibNames.some(name => name === quib.name);

  const selectQuibTabOfQuib = (quib: Quib) => {
    if (quibInSelectedQuibs(quib)) {
      setSelectedQuibNames(selectedQuibNames.filter(
        n => n !== quib.name
      ))
    } else {
      setSelectedQuibNames([
        ...selectedQuibNames,
        quib.name
      ])
    }
  }

  return <UseSignal initialArgs={props.initialQuibs} signal={props.signal}>
    {
      (_, quibs) => <div>
          <div style={{
            display: "flex", borderWidth: "0 0 0 1px", borderColor: "rgb(190, 189, 189)",
            borderStyle: "solid"
          }}>
            {
              (quibs ? quibs : []).map((quib) =>
                <QuibTab onClick={() => selectQuibTabOfQuib(quib)}
                         className={quibInSelectedQuibs(quib) ? "active" : ""}>
                  <div style={{marginRight: "8px", marginLeft: "8px"}}>{quib.name}</div>
                </QuibTab>
              )
            }

          </div>
          <div style={{display: "flex", flexWrap: "wrap"}}>
            {
              quibs &&
              selectedQuibNames.map(name => {
                const quib = quibs.find(q => q.name === name);
                return quib && <div style={{margin: "10px"}}>
                  <QuibEditor onQuibChange={props.onChangeQuib} quib={quib} requester={props.requester}/>

                </div>;
              })
            }
          </div>

        </div>
    }

  </UseSignal>
}

export class QuibsEditorWidget extends ReactWidget {

  private readonly requester: IRequester;
  private quibs: Quib[];
  private _quibsSignal = new Signal<this, Quib[]>(this);

  constructor(quibs: Quib[], requester: IRequester) {
    super();
    this.quibs = quibs;
    this.requester = requester;
  }

  changeQuib = (quib: Quib) => {
    if (this.quibs.find(q => q.name === quib.name) !== undefined) {
      this.quibs = this.quibs.map(q => q.name === quib.name ? quib : q);
      this._quibsSignal.emit(this.quibs)
    }
  }

  render() {
    return <div style={{marginLeft: "72px"}}><QuibsEditor signal={this._quibsSignal}
                                                          onChangeQuib={this.changeQuib}
                                                          initialQuibs={this.quibs}
                                                          requester={this.requester} /></div>
  }
}
