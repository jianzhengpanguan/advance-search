import os
import PyPDF2
import gpt
import utils
import speech
import argparse
from typing import List

_OUTPUT_FORMAT = """
    [Scene: ...]
    Host: "Welcome to our channel! Today, we're going to dive into the world of ..."
    [Scene: ...]
    Host: "..."
    ...
    [Scene: ...]
    Host: "And that's it for today's video! We hope you enjoyed learning about ..."
"""

def add_introduction(scripts: List[str]) -> str:
    prompt = f"""
    We wrote multiples sections's script for a YouTube video based on the following text:
    ```
    {scripts}
    ```
    Create an attractive introduction for the video:
    1. Create anticipation: Tease what's coming up in the video to keep viewers interested.
    2. Keep it short: Aim for 5-10 seconds. Longer intros may cause viewers to lose interest.
    3. Clearly state the video's purpose: Let viewers know what they'll learn or experience in the video.
    4. Use a hook: Start with an intriguing question, statement, or preview of the video's content.
    5. keep them in the same format.
    ```
    [Scene: ...]
    Host: "..."
    ...
    ```
    """
    return gpt.openai_request(prompt, utils.ModelType.advance_model)


def enrich_with_explanation(article: str, script: str) -> str:
    prompt = f"""
    We wrote a script for a YouTube video based on the following text:
    ```
    {article}
    ```
    The script:
    ```
    {script}
    ```
    The script is good but without explanation. 
    Please also add more explanation from the doc for each premise.
    keep them in the format:
    ```
    {_OUTPUT_FORMAT}
    ```

    Keep it funny but with details. 
    """
    return gpt.openai_request(prompt, utils.ModelType.advance_model)


def generate_script(section: str) -> str:
    prompt = f"""
    I want to create a youtube video.
    Write a script for a YouTube video based on the following section:
    ```
    {section}
    ```
    Help me generate the script for the video, make it funny,
    but make sure you mentioned every premises and its explanation.
    keep them in the format:
    ```
    {_OUTPUT_FORMAT}
    ```
    """
    return gpt.openai_request(prompt, utils.ModelType.advance_model)


def split_pdf_by_delimiter(pdf_path, delimiter='. . .'):
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        all_text = ''
        
        # Extract text from each page
        for page in reader.pages:
            text = page.extract_text()
            if text:
                all_text += text + '\n'  # Append text from each page

    # Split text by delimiter
    return all_text.split(delimiter)

def main():
    parser = argparse.ArgumentParser(description='Process the flags.')
    parser.add_argument('-folder', '--folder_path', type=str, default='./data/6. Trump shooter motive', help='Folder path')
    args = parser.parse_args()
    folder_path = args.folder_path
    file_path = f"{folder_path}/medium.pdf"
    script_path = f"{folder_path}/youtube_script.txt"
    subtitle_path = f"{folder_path}/youtube_subtitle.txt"
    audio_path = f"{folder_path}/youtube_audio"
    # Ensure the directory exists.
    os.makedirs(audio_path, exist_ok=True)

    sections = split_pdf_by_delimiter(file_path)
    enriched_scripts = []
    # Process each section
    for index, section in enumerate(sections):
        print(f"Section {index + 1}:")
        print(section[:100])  # Print the first 100 characters of each section for preview
        print('----------------\n')
        script = generate_script(section)
        print(script[:100])  # Print the first 100 characters of the script for preview
        print('----------------\n')
        enriched_script = enrich_with_explanation(section, script)
        print(enriched_script[:100])  # Print the first 100 characters of the script for preview
        print('----------------\n')
        enriched_scripts.append(enriched_script)
    # Add introduction.
    intro = add_introduction(enriched_scripts)
    enriched_scripts = [intro] + enriched_scripts
    with open(script_path, "w") as f:
        f.write("\n".join(enriched_scripts))
    with open(script_path, "r") as f:
        enriched_scripts = "\n".join(f.readlines()).split("\n")
    
    # Only keep the host's dialogue.
    dialogue = []
    for index, script in enumerate(enriched_scripts):
        lines = script.split("\n")
        for line in lines:
            # Skip the empty line.
            if not line.strip() or "..." in line or "```" in line:
                continue
            # Skip the scene.
            if "Scene" in line:
                continue
            # Skip the "Welcome to our channel!" between sections.
            if index != 0 and "Welcome" in line:
                continue
            # Skip the "And that's it for today's video" between sections.
            if index != len(enriched_scripts) - 1 and "today" in line:
                continue
            parsed_line = line.replace("Host", "").replace("\"", "").replace(":", "").strip()
            dialogue.append(f"{parsed_line}")
    with open(subtitle_path, "w") as f:
        f.write("\n".join(dialogue))

    with open(subtitle_path, "r") as f:
        dialogue = "\n".join(f.readlines()).split("\n")
    index = 0
    for line in dialogue:
        if not line.strip():
            continue
        audio = speech.generate(line)
        with open(f"{audio_path}/{index}.mp3", "wb") as f:
            for chunk in audio:
                f.write(chunk)
        index += 1


if __name__ == "__main__":
    main()
