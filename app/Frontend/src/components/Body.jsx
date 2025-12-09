import { useState, useEffect } from "react";
import "./styles/Body.css";
import GetAPI from "./Terms/GetAPI";
import Popup from "./Terms/Popup";
import Main from "./Main";

export default function Body() {
    const [accepted, setAccepted] = useState(false);
    const [enter, setEnter] = useState(false);

    useEffect(() => {
        chrome.storage.sync.get("accepted", (result) => {
            const acceptedValue = result?.accepted || false;
            setAccepted(acceptedValue);
        });
    }, []);

    useEffect(() => {
        chrome.storage.sync.get("enter", (result) => {
            const enterValue = result?.enter || false;
            setEnter(enterValue);
        });
    }, []);

    if (accepted === null) return <div>Loading...</div>;
    if (enter === null) return <div>Loading...</div>;

    if(!accepted){
        return (
            <div className="body-container">
                <Popup setAccepted={setAccepted} />
            </div>
        )
    }
    else if(!enter){
        return (
            <div className="body-container">
                <GetAPI setEnter={setEnter} />
            </div>
        )
    }
    else {
        return (
            <div className="body-container">
                <Main/>
            </div>
        )
    }

    return (
        <div className="body-container">
            <Main/>
        </div>
    )
}
