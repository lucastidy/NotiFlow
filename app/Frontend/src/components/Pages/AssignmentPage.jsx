import { useState, useEffect } from "react";
import Assignment from "./elements/Assignment"
import "./styles/AssignmentPage.css"
import axios from "axios";

/**
 * AssignmentPage Component
 *
 * Loads and displays assignment data grouped by course. Pulls saved
 * assignment information from chrome.storage on mount, renders each
 * course section with its list of assignments, and provides a "Reparse"
 * button to fetch fresh assignment data from the backend API.
 *
 * Contains local state for:
 *   - assignments (array/object): Parsed assignment data for display.
 *
 * @returns {JSX.Element} The full assignment page UI with course headers,
 *                        assignment cards, and a reparse button.
 */
export default function AssignmentPage() {
  const [assignments, setAssignments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    chrome.storage.sync.get(["assignments"], (result) => {
      if (result.assignments) {
        setAssignments(result.assignments || []);
      }
    });
  }, []);

  /**
  * Saves data to chrome.storage.sync using a Promise wrapper.
  *
  * @param {Object} data - The key/value pairs to store in chrome.storage.
  * @returns {Promise<void>} Resolves once chrome.storage has finished writing.
  */
  function storageSet(data) {
      return new Promise((resolve) => {
          chrome.storage.sync.set(data, () => {
              resolve();
          });
      });
  }

  
  function storageGet(keys) {
    return new Promise((resolve) => {
        chrome.storage.sync.get(keys, (result) => {
            resolve(result);
        });
    });
  }
  
  /**
   * Re-fetches assignment data from the backend server and updates both
   * chrome.storage and local state.
   *
   * Used when the user clicks the "Reparse" button to refresh assignments.
   *
   * @returns {Promise<void>} Resolves after syncing storage and state.
   */ 
  const reparse = async () => {
    setIsLoading(true);
    try {
      const result = await storageGet("token");
      const token = result.token;

      const assignments = await axios.get("http://localhost:8080/api/assignments",{
        params: { token }
      })
      const fetchedAssignments = assignments.data;
      
      await storageSet({ assignments: fetchedAssignments });
      setAssignments(fetchedAssignments);
      console.log("Stored data:", fetchedAssignments);
    } catch(error){
        console.log("Error reparsing")
    } finally {
        setIsLoading(false);
    }
  }

  return (
      <div className="assignment-page">
        {Object.entries(assignments).map(([className, classData], i) => (
            <div key={i}>
            <div className="assignment-class">{className}</div>
            {classData.assignments.flat(1).map(item=>(
                <div> 
                    <Assignment
                        assignment={item[0]}
                        date={item[1]}
                        time={item[2]}
                    />
                </div>
            ))}
            <hr className="assignment-page-line"></hr>
            </div>
        ))}

        <div className="assignment-button-container">
            <button className="assignment-button" onClick={reparse} disabled={isLoading}>
              {isLoading ? "Reparsing..." : "Reparse"}
            </button>
            {isLoading && (
              <div className="assignment-loading-indicator">
                <span className="assignment-loading-spinner" aria-hidden="true"></span>
                <span>Updating assignments</span>
              </div>
            )}
        </div>
      </div>
  );
}
