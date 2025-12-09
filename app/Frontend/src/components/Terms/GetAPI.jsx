import { useState } from "react"
import "./styles/GetAPI.css"
import { useEffect } from "react";
import axios from "axios";

/**
 * GetAPI Component
 *
 * Handles the user’s initial API token entry required to access class data
 * from the backend. Displays instructions, accepts the token, validates it,
 * and then triggers backend requests to fetch course and final exam data.
 * 
 * @returns {JSX.Element} The complete UI for token entry and submission.
 */
export default function GetAPI({ setEnter }){
    const [APIKEY, setAPIKEY] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [classes, setClasses] = useState([]);

    /**
     * Saves the provided key/value pairs to chrome.storage.sync.
     *
     * Chrome storage is callback-based; this wrapper converts it into a Promise
     * so that async/await can be used cleanly throughout the component.
     *
     * @param {Object} data - The data object to store.
     * @returns {Promise<void>} Resolves when chrome.storage has finished writing.
     */
    function storageSet(data) {
        return new Promise((resolve) => {
            chrome.storage.sync.set(data, () => {
                resolve();
            });
        });
    }

    /**
     * Validates and submits the user's API token, then fetches all required
     * backend data (courses and final exams).
     * If any backend call fails, displays an error instructing the user to retry.
     *
     * @returns {Promise<void>} Resolves after all data is fetched and stored.
     */
    const handleEnter = async () => {
        if (!APIKEY.trim()) {
            setErrorMessage("Please paste your API token before continuing.");
            return;
        } else {
            // Call backend using flask to retrive objects from localhost
            try {
                const courseData = await axios.get("http://localhost:8080/api/courses",{
                    params: { token: APIKEY.trim() }
                })
                const fetchedCourses = courseData.data;
                
                await storageSet({ courses: fetchedCourses });
                setClasses(fetchedCourses);
                console.log("Stored data:", fetchedCourses);

                const finalExamData = await axios.get("http://localhost:8080/api/finalexam", {
                    params: {
                        course: classes,
                    }});
                const fetchedFinals = finalExamData.data;

                await storageSet({ finals: fetchedFinals });
                console.log("Stored data:", fetchedFinals);

            } catch(error){
                setErrorMessage("cannot access APIKEY, try again")
            }
            chrome.storage.sync.set({ enter: true, token: APIKEY.trim() }, () => {
            setErrorMessage('');
            setEnter(true);
        })
        }
    }

    return(
        <div className="getapi-container">
            <div className="getapi-title">API Token</div>
            <div className="getapi-subtitle">To get access to relevant class information, we need your API token</div>
            <hr className="getapi-line"></hr>
            <div className="getapi-text">Instructions:</div>
            <ol className="getapi-instructions">
                <li>Login to Canvas on your browser</li>
                <li>Click on Account then go to Settings</li>
                <li>Scroll down until you see <strong>Approved Integrations</strong></li>
                <li>Click <strong>New Access Token</strong></li>
                <li>Set it to the Maximum Expiry Date and Time and purpose for Notiflow</li>
                <li>Click <strong>Generate Token and Paste the token below</strong></li>
            </ol>
            <div className="getapi-input-container">
                <div className="getapi-input-key">Key:</div>
                <input
                    type="text"
                    id="simple-textbox"
                    value={APIKEY}
                    className="getapi-input"
                    onChange={(event) => setAPIKEY(event.target.value)}
                    aria-invalid={!!errorMessage}
                    aria-describedby="getapi-error"
                />
                <button className="getapi-input-button" onClick={handleEnter}>ENTER</button>
            </div>
            {errorMessage && (
                <p id="getapi-error" className="getapi-error">{errorMessage}</p>
            )}
        </div>
        
    )
}
