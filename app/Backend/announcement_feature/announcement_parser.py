import os
import re

from openai import OpenAI


class AnnouncementParser:
    """
    Utility class for parsing Canvas announcement text and extracting midterm dates.

    The class splits announcement text into sentences, filters for those
    mentioning "midterm", and then uses the OpenAI API to extract
    date or date-time values in ISO 8601 format.

    This helper is meant to be stateless — all logic resides in the static
    method `extract_midterm_dates`.
    """

    @staticmethod
    def extract_midterm_dates(announcements: str, posted_at: str):
        """
        Extracts midterm dates from a block of announcement text using regex filtering
        and an OpenAI model for natural-language date parsing.

        Args:
            announcements (str): Full announcement text (may contain multiple sentences).
            posted_at (str): ISO timestamp string for when the announcement was posted;
                passed to the model for context.

        Returns:
            str | None: A stripped ISO 8601 date or date-time string returned by
            the model, or `None` if no sentences mention "midterm".

        Raises:
            openai.OpenAIError: If the API call fails or the response is invalid.

        Notes:
            * Sentences are split on punctuation boundaries using
              `re.split(r'(?<=[.!?])\\s+')`.
            * If no sentence includes "midterm" (case-insensitive),
              the function returns `None` without calling the API.
            * The OpenAI model (gpt-4o-mini) is prompted to output only ISO-formatted dates.
        """
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        # keep only lines mentioning "midterm"
        sentences = re.split(r"(?<=[.!?])\s+", announcements)

        # filter sentences w/ midterm
        midterm_sentences = [
            s.strip() for s in sentences if re.search(r"\bmidterm\b", s, re.IGNORECASE)
        ]

        if not midterm_sentences:
            return None

        # DEBUG
        # print(midterm_entries)

        prompt_body = "\n".join(
            f"Posted at {posted_at}: {s}" for s in midterm_sentences
        )

        prompt = (
            "Extract all midterm dates or date-times mentioned below.\n"
            "Output ONLY in ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM).\n"
            "When analyzing, if a date is found in a sentence, stop and return it.\n"
            "If no date is found, output nothing. Do not write explanations or text.\n\n"
            f"{prompt_body}"
        )

        response = client.responses.create(
            model="gpt-4o-mini", input=prompt, max_output_tokens=250
        )

        return response.output_text.strip()
