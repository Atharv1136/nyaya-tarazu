import os
import sys
import time
from datetime import date
from dotenv import load_dotenv

# Add workspace directory to python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.services.llm import extract_facts, generate_briefs, answer_lookup
from backend.models.schemas import LegalSection

load_dotenv()

def run_tests():
    print("==================================================")
    # 1. Test fact extraction
    print("1. Testing extract_facts...")
    narrative = (
        "On 15 August 2024, Ramesh Patel entered the house of Suresh Joshi in Ahmedabad, "
        "carrying an iron rod, and attacked Suresh Joshi due to a property dispute, causing severe skull fractures. "
        "Sunita Joshi witnessed this."
    )
    start = time.time()
    try:
        facts = extract_facts(narrative, hint_date=date(2024, 8, 15))
        print(f"Success in {time.time() - start:.2f}s!")
        print("Parties:", facts.parties)
        print("Offence Type:", facts.offence_type)
        print("Intent:", facts.intent)
        print("Weapon/Method:", facts.weapon_or_method)
        print("Injury:", facts.injury)
        print("Code Era:", facts.code_era)
    except Exception as e:
        print(f"Failed: {e}")
        return

    print("--------------------------------------------------")

    # Mock some retrieved sections
    mock_sections = [
        LegalSection(
            chunk_id="chk1",
            act_name="BNS",
            section_number="103",
            section_title="Punishment for murder",
            chunk_text="Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine.",
            code_era="new",
            page_number=1,
            cross_references=["IPC 302"]
        )
    ]

    # 2. Test brief generation
    print("2. Testing generate_briefs...")
    start = time.time()
    try:
        prosecution, defense = generate_briefs(facts, mock_sections)
        print(f"Success in {time.time() - start:.2f}s!")
        print("Prosecution Issues:", prosecution.issues)
        print("Defense Issues:", defense.issues)
        print("Prosecution Prayer:", prosecution.prayer)
        print("Defense Prayer:", defense.prayer)
    except Exception as e:
        print(f"Failed: {e}")
        return

    print("--------------------------------------------------")

    # 3. Test lookup Q&A
    print("3. Testing answer_lookup...")
    start = time.time()
    try:
        answer = answer_lookup("What is the punishment for murder under BNS?", mock_sections)
        print(f"Success in {time.time() - start:.2f}s!")
        print("Answer:", answer)
    except Exception as e:
        print(f"Failed: {e}")
        return
    print("==================================================")

if __name__ == "__main__":
    run_tests()
