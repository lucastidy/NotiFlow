import "./styles/ClasstimeCard.css"

/**
 * ClasstimeCard Component
 *
 * Displays a saved class entry in a styled card format. Shows:
 *   - class name
 *   - selected meeting days (converted to full names)
 *   - scheduled start and end times
 *
 * Also provides Edit and Delete action buttons, with behavior controlled
 * by parent-passed callback functions.
 *
 * @returns {JSX.Element} A card displaying class info and action controls.
 */
export default function ClasstimeCard({ classData, onEdit, onDelete }) {
    const { className, days, startTime, endTime } = classData;

    /**
    * Maps weekday shorthand keys (M, Tu, W, Th, F)
    * to their full, readable weekday names.
    *
    * Used to convert the stored day booleans into user-friendly text.
    */
    const dayNames = {
        M: "Monday",
        Tu: "Tuesday",
        W: "Wednesday",
        Th: "Thursday",
        F: "Friday"
    };

    /**
    * Produces a comma-separated string of all selected meeting days.
    * Example: "Monday, Wednesday, Friday"
    */
    const selectedDays = Object.entries(days)
        .filter(([_, checked]) => checked)
        .map(([day]) => dayNames[day])
        .join(", ");

    return (
        <div className="classtime-card">
            <div className="classtimecard-container">
                <div className="classtimecard-classname">{className}</div>
                <div className="classtimecard-detail"> <strong>Dates:</strong> {selectedDays}</div>
                <div className="classtimecard-detail"> <strong>Time:</strong> {startTime} – {endTime}</div>
            </div>
            
            <div className="classtime-buttons">
                <button className="classtime-editbutton" onClick={onEdit}>Edit</button>
                <button className="classtime-deletebutton" onClick={onDelete}>Delete</button>
            </div>
            <hr className="clastimecard-line"></hr>
        </div>
    );
}
