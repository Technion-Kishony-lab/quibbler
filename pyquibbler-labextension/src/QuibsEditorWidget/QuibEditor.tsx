import React, {KeyboardEvent, useState} from 'react';
import {Quib} from "./types";
import {Button} from "../button";
import CloseSvg from "../../images/close.svg";
import {IRequester} from "../requester";
import {showErrorOnFailure} from "../utils";


export const QuibEditor = (props: {quib: Quib,
  onQuibChange: (quib: Quib) => void,
  requester: IRequester}) => {

  const [dirty, setDirty] = useState(false);

  const changeOverride = (overrideIndex: number, left: string, right: string) => {
    setDirty(true);

    const newOverrides = [...props.quib.overrides!];
    newOverrides[overrideIndex] = {left, right};
    props.onQuibChange({
      ...props.quib,
      overrides: newOverrides,
      synced: false
    });
  }

  const addOverride = () => {
    props.requester.cancelPendingRequests();
    console.log("Canceled pending requests");
    const newQuib = {
      ...props.quib,
      overrides: [...props.quib.overrides || [], {
        left: "",
        right: ""
      }],
      synced: false
    }
    console.log("Adding override from quib editor")
    props.onQuibChange(newQuib);
  }

  const removeOverride = async (overrideIndex: number) => {
    const newOverrides = [...props.quib.overrides!];
    newOverrides.splice(overrideIndex, 1);

    console.log("Removing override from quib editor")
    const quib = await showErrorOnFailure(props.requester.request("removeAssignment", {
      quib_id: props.quib.id,
      index: overrideIndex
    }));
    props.onQuibChange(quib);
  }

  const saveQuib = async () => {
    console.log("Saving quib from quib editor")
    await showErrorOnFailure(props.requester.request("saveQuib", {
      quib_id: props.quib.id,
    }
    ))
    props.onQuibChange({
      ...props.quib,
      synced: true
    });
  }

  const loadQuib = async () => {
    console.log("Loading quib from quib editor")
    const quib = await showErrorOnFailure(props.requester.request("loadQuib", {
        quib_id: props.quib.id,
      }
    ));
    props.onQuibChange(quib);
  }

  const upsertOverride = async (index: number) => {
    if (!dirty) {
      return;
    }

    const override = props.quib.overrides![index];
    if (override.right === "") {
      return;
    }

    console.log("Upserting assignment");
    setDirty(false);
    const quib = await showErrorOnFailure(props.requester.request("upsertAssignment", {
      quib_id: props.quib.id,
      index: index,
      raw_override: props.quib.overrides![index]
    }));
    props.onQuibChange(quib);
  }

  const onKeyPress = async (index: number, e: KeyboardEvent<HTMLInputElement>) => {
    e.key === "Enter" && await upsertOverride(index);
  }

  return <div>
          <div style={{marginBottom: "4px", fontWeight: "bold", fontSize: "75%",
            color: "var(--jp-mirror-editor-variable-color)"}}>{props.quib.repr}</div>
          {
            props.quib.overrides === null ?
              <span style={{fontWeight: "bold"}}>Overrides cannot be presented as text.</span> :
              <div>
                {
                  props.quib.overrides.map((override, i) =>
                      <div style={{display: "flex", height: "1.6em",
                        fontSize: "var(--jp-code-font-size)", fontFamily: "var(--jp-code-font-family)",
                        marginBottom: "0.4em"
                      }}>
                    <input className="bp3-input" value={override.left}
                           style={{fontFamily: 'inherit', fontSize: 'inherit', height: 'inherit', width: "80px",
                             color: "var(--jp-mirror-editor-variable-color)",
                             background: "var(--jp-cell-editor-background)",
                             border: "var(--jp-border-width) solid var(--jp-cell-editor-border-color)"}}
                           onChange={e => changeOverride(i, e.target.value,
                             override.right)} onBlur={() => upsertOverride(i)} onKeyPress={
                               (e) => onKeyPress(i, e)} />
                    <div style={{display: "flex", justifyContent: "center", flexDirection: "column",
                      marginLeft: "4px", marginRight: "4px",
                      fontFamily: 'inherit', fontSize: 'inherit', height: 'inherit',
                             color: "var(--jp-mirror-editor-variable-color)"}}>
                      <div>=</div>
                    </div>
                    <input className="bp3-input" value={override.right}
                           style={{fontFamily: 'inherit', fontSize: 'inherit', height: 'inherit', width: "120px",
                             color: "var(--jp-mirror-editor-variable-color)",
                             background: "var(--jp-cell-editor-background)",
                             border: "var(--jp-border-width) solid var(--jp-cell-editor-border-color)"}}
                           onChange={e => changeOverride(i, override.left,
                             e.target.value)} onBlur={() => upsertOverride(i)} onKeyPress={(e) =>
                      onKeyPress(i, e)} />
                    <div onClick={() => removeOverride(i)} className="jp-icon-hover"
                         style={{display: "flex", marginLeft: "4px"}} dangerouslySetInnerHTML={{__html: CloseSvg}}/>
                  </div>)
                }
                <div style={{display: "flex", marginTop: "10px"}}>
                  <Button style={{marginRight: "4px",
                    display: "inline-flex", alignItems: "center", height: "6px", fontSize: "65%"}}
                          disabled={props.quib.synced}
                          onClick={saveQuib}>Save</Button>
                  <Button style={{marginRight: "4px",
                    display: "inline-flex", alignItems: "center", height: "6px", fontSize: "65%"}}
                          disabled={props.quib.synced}
                          onClick={loadQuib}>Load</Button>
                  <Button style={{
                    display: "inline-flex", alignItems: "center", height: "6px", fontSize: "65%"}}
                      onClick={addOverride}>Add Override</Button>
                </div>
              </div>
          }
    </div>
}