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
    if (override.left === "" || override.right === "") {
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
          <div style={{ fontSize: "13pt", marginBottom: "4px", fontWeight: "bold"}}>{props.quib.name}</div>
          <div style={{display: "flex"}}>
            <Button style={{marginBottom: "6px", marginRight: "4px"}}
                    disabled={props.quib.synced}
                    onClick={saveQuib}>Save</Button>
            <Button style={{marginBottom: "6px", marginRight: "4px"}}
                    disabled={props.quib.synced}
                    onClick={loadQuib}>Load</Button>
            <div style={{display: "flex", justifyContent: "center", flexDirection: "column"}}>
              {props.quib.synced ? "Synced (fs)" : "Unsynced (fs)"}
            </div>
          </div>
          {
            props.quib.overrides === null ?
              <span style={{fontWeight: "bold"}}>Overrides could not be loaded (perhaps they are in binary?)</span> :
              <div>
                <div style={{marginBottom: "7px"}}>
                  <b>Overrides</b>
                </div>
                {
                  props.quib.overrides.map((override, i) => <div style={{display: "flex"}}>
                    <div style={{height: "35px", marginRight: "4px"}}>
                      <input className="bp3-input" value={override.left}
                             onChange={e => changeOverride(i, e.target.value,
                               override.right)} onBlur={() => upsertOverride(i)} onKeyPress={
                                 (e) => onKeyPress(i, e)} />
                    </div>
                    <div style={{display: "flex", justifyContent: "center", flexDirection: "column", height: "30px"}}>
                      <div>=</div>
                    </div>
                    <div style={{height: "35px", marginLeft: "4px", marginRight: "4px"}}>
                      <input className="bp3-input" value={override.right}
                             onChange={e => changeOverride(i, override.left,
                               e.target.value)} onBlur={() => upsertOverride(i)} onKeyPress={(e) =>
                        onKeyPress(i, e)} /></div>
                    <div onClick={() => removeOverride(i)} className="jp-icon-hover"
                         style={{display: "flex", height: "30px"}} dangerouslySetInnerHTML={{__html: CloseSvg}}/>
                  </div>)
                }
                <Button onClick={addOverride}
                        style={{backgroundColor: "var(--jp-brand-color1)", marginTop: "4px"}}>
                  Add Override
                </Button>
              </div>
          }
    </div>
}