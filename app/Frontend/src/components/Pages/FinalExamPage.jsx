import { useEffect } from "react";
import FinalExam from "./elements/FinalExam"
import "./styles/FinalExamPage.css"
import { useState } from "react";
import axios from "axios";


export default function FinalExamPage(){
    const [finals, setFinals] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        chrome.storage.sync.get(["finals"], (result) => {
            if (result.finals) {
                setFinals(result.finals || []);
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
            const {courses} = await chrome.storage.sync.get("courses");
            const finals = await axios.get("http://localhost:8080/api/finalexam",{
                params: { course: courses }
            })
            const fetchedFinals = finals.data;
            
            await storageSet({ finals: fetchedFinals });
            setFinals(fetchedFinals);
            console.log("Stored data:", fetchedFinals);
        } catch(error){
            console.log("Error reparsing")
        } finally {
            setIsLoading(false);
        }
    }
   
    return(
        <div className="finalexam-page">
            {finals.map((session) => (
                <FinalExam
                    className={session.course + " Final"}
                    date={session.date}
                    begin_date_time={session.begin_date_time}
                    end_date_time={session.end_date_time}
                    location={session.location}
                />
            ))}
            <div className="final-button-container">
                <button className="final-button" onClick={reparse} disabled={isLoading}>
                    {isLoading ? "Reparsing..." : "Reparse"}
                </button>
                {isLoading && (
                    <div className="final-loading-indicator">
                        <span className="final-loading-spinner" aria-hidden="true"></span>
                        <span>Updating finals</span>
                    </div>
                )}
            </div>
        </div>
    )
}