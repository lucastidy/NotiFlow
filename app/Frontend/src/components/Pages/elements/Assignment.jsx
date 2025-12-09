import "./styles/Assignment.css"
/**
 * Assignment Component
 *
 * Displays a single assignment as a styled card, including:
 *  - assignment name
 *  - due date
 *  - due time
 *
 * @param {string} assignment - The title or name of the assignment.
 * @param {string} date - The formatted due date to display.
 * @param {string} time - The formatted due time to display.
 *
 * @returns {JSX.Element} A styled assignment card displaying the provided details.
 */

export default function Assignment(props){
    const { assignment, date, time } = props;

    return (
        <div className="assignment-card">
            <div className="assignment-container">
                <div className="assignment-name">{assignment}</div>
                <div className="assignment-detail">
                    <strong>Due Date: </strong> {date}
                </div>
                <div className="assignment-detail">
                    <strong>Due Time:</strong> {time}
                </div>
            </div>
        </div>
    )
}
