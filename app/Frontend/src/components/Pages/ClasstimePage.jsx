import "./styles/ClasstimePage.css"
import Classtime from "./elements/Classtime.jsx"
import ClasstimeCard from "./elements/ClasstimeCard.jsx";
import { useState } from "react";
import { useEffect } from "react";

/**
 * ClasstimePage Component
 *
 * Manages the list of class entries, including creation, editing, and deletion.
 * Loads class data from chrome.storage, displays either the class input form
 * or existing class cards depending on UI state, and keeps all data synced with storage.
 *
 * @returns {JSX.Element} The rendered ClasstimePage interface.
 */
export default function ClasstimePage() {
    // List of all saved classes
    const [classes, setClasses] = useState([]);

    // Whether the class input form is currently visible
    const [showInput, setShowInput] = useState(true);

    // Index of the class being edited (null if not editing)
    const [editingIndex, setEditingIndex] = useState(null);

    /**
     * Loads saved class data from chrome.storage on initial mount.
     */
    useEffect(() => {
      chrome.storage.sync.get("classData", (result) => {
        if (result.classData) {
          setClasses(result.classData);
        }
      });
    }, []);

    /**
     * Toggles visibility of the input form based on whether any classes exist.
     * Input is shown when there are no classes and hidden otherwise.
     */
    useEffect(() => {
      if (classes.length === 0) {
        setShowInput(true);
      } else {
        setShowInput(false);
      }
    }, [classes]);
  
  /**
   * Saves a class object to the class list.
   *
   * If `editingIndex` is not null, the function updates the existing class entry
   * at that index. Otherwise, it appends the new class to the list.
   *
   * After updating, the new class list is saved to chrome.storage and the local
   * state is updated.
   *
   * @param {Object} classObj - The class data being saved.
   */
  function handleSave(classObj) {
    if (editingIndex !== null) {
      const updated = [...classes];
      updated[editingIndex] = classObj;
      setClasses(updated);
      chrome.storage.sync.set({ classData: updated });
      setEditingIndex(null);
    } else {
      const updated = [...classes, classObj];
      setClasses(updated);
      chrome.storage.sync.set({ classData: updated });
    }
    setShowInput(false);
  }
  /**
   * Deletes a class entry at the specified index.
   *
   * This function removes the class at the given index from the `classes` list,
   * updates the React state, and persists the updated list to `chrome.storage`.
   *
   * @param {number} index - The index of the class to delete.
   */
  function handleDelete(index) {
    const updated = classes.filter((_, i) => i !== index);

    setClasses(updated);
    chrome.storage.sync.set({ classData: updated });
  }

  /**
   * Enables edit mode for a specific class entry.
   *
   * Sets the `editingIndex` to the provided index so the UI knows which class
   * is being edited. Also ensures that the input form becomes visible by
   * setting `showInput` to true.
   *
   * @param {number} index - The index of the class to edit.
   */
  function handleEdit(index) {
    setEditingIndex(index);
    setShowInput(true);
  }

  // async function generateIcal(){
  //   const {courses} = await chrome.storage.sync.get("classData");
  //   await axios.get("http://localhost:8080/api/finalexam",{
  //     params: { "classData[]" : courses }
  //   })
  // }

  return (
       <div className="classtime-page">
      {showInput && (
        <Classtime
          initialData={editingIndex !== null ? classes[editingIndex] : null}
          onSave={handleSave}
        />
      )}

      {!showInput && classes.map((c, index) => (
        <ClasstimeCard
          key={index}
          classData={c}
          onEdit={() => handleEdit(index)}
          onDelete={() => handleDelete(index)}
        />
      ))}

      {!showInput && (
        <button className="add-another-btn" onClick={() => setShowInput(true)}>
          Add Another Class
        </button>
      )}

      {/* {!showInput && (
        <button className="add-another-btn" onClick={generateIcal}>
          Generate ICal
        </button>
      )} */}

    </div>
  );
}

