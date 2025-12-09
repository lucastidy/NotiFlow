import { useEffect } from "react";
import Midterm from "./elements/Midterm"
import "./styles/MidtermPage.css"
import { useState } from "react";
import axios from "axios";

const info = [
  {
    "begin_date_time": "12:00:00",
    "course": "MATH 253",
    "date": "2025/10/15",
    "end_date_time": "1:00:00",
    "event_type": "Midterm"
  }
];

export default function MidtermPage(){
    const [midterms, setMidterms] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        chrome.storage.sync.get(["midterms"], (result) => {
            if (result.midterms) {
                setMidterms(result.midterms || []);
            }
        });
    }, []);

    /**
     * 
     * @param {*} data 
     * @returns 
     */
    function storageSet(data) {
        return new Promise((resolve) => {
            chrome.storage.sync.set(data, () => {
                resolve();
            });
        });
    }

    const reparse = async () => {
        setIsLoading(true);
        try {
            const {token} = await chrome.storage.sync.get("token");
            const midterms = await axios.get("http://localhost:8080/api/announcements",{
                params: { token }
            })
            const fetchedMidterms = midterms.data;
            
            await storageSet({ midterms: fetchedMidterms });
            setMidterms(fetchedMidterms);
            console.log("Stored data:", fetchedMidterms);
        } catch(error){
            console.log("Error reparsing")
        } finally {
            setIsLoading(false);
        }
    }
   

    return(
        <div className="midterm-page">
            {midterms.map((session) => (
                <Midterm
                    className={session.course + " Midterm"}
                    date={session.date}
                    begin_date_time={session.begin_date_time}
                    end_date_time={session.end_date_time}
                />
            ))}
            <div className="midterm-button-container">
                <button className="midterm-button" onClick={reparse} disabled={isLoading}>
                    {isLoading ? "Reparsing..." : "Reparse"}
                </button>
                {isLoading && (
                    <div className="midterm-loading-indicator">
                        <span className="midterm-loading-spinner" aria-hidden="true"></span>
                        <span>Updating midterms</span>
                    </div>
                )}
            </div>
        </div>
    )
}