import "./styles/ComponentSelect.css"
import ClasstimePage from "./Pages/ClasstimePage"
import AssignmentPage from "./Pages/AssignmentPage"
import FinalExamPage from "./Pages/FinalExamPage"
import MidtermPage from "./Pages/MidtermPage"

/**
 * ComponentSelect Component
 *
 * Acts as a simple router for the popup UI. Renders one of the main
 * pages—Classes, Final Exams, Assignments, or Midterms—based on the
 * currently selected tab passed in via props.
 *
 * @returns {JSX.Element|null} The selected page component, or null if no match.
 */
export default function ComponentSelect(props){
    if(props.selectedTab == "Classes"){
        return <ClasstimePage/>
    }
    if(props.selectedTab == "Finals"){
        return <FinalExamPage/>
    }
    if(props.selectedTab == "Assignments"){
        return <AssignmentPage/>
    }
    if(props.selectedTab == "Midterms"){
        return <MidtermPage/>
    }
}

