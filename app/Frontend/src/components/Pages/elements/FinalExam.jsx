import "./styles/FinalExam.css"

/**
 * FinalExam Component
 *
 * Renders a styled card displaying final exam information for a course.
 * Shows:
 *   - course name
 *   - exam date
 *   - exam time
 *   - exam location
 * 
 * @returns {JSX.Element} A card UI element displaying the exam details.
 */
export default function FinalExam(props){
    const { className, date, begin_date_time, end_date_time, location } = props;

    return (
        <div className="finalexam-card">
            <div className="finalexam-container">
                <div className="finalexam-name">{className}</div>
                <div className="finalexam-detail">
                    <strong>Date:</strong> {date}
                </div>
                <div className="finalexam-detail">
                    <strong>Start Time:</strong> {begin_date_time}
                </div>
                <div className="finalexam-detail">
                    <strong>End Time:</strong> {end_date_time}
                </div>
                <div className="finalexam-detail">
                    <strong>Location:</strong> {location}
                </div>
            </div>
            <hr className="finalexam-line"></hr>
        </div>
    )
}
