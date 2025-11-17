import os

def save_tree(start_path, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        for root, dirs, files in os.walk(start_path):
            # --- Skip venv/.venv folders ---
            dirs[:] = [d for d in dirs if d not in ("venv", ".venv")]

            level = root.replace(start_path, "").count(os.sep)
            indent = "│   " * level + "├── "
            f.write(f"{indent}{os.path.basename(root)}/\n")
            
            sub_indent = "│   " * (level + 1) + "├── "
            for file in files:
                f.write(f"{sub_indent}{file}\n")

if __name__ == "__main__":
    folder_to_scan = r"."   # current directory
    output_txt = "folder_structure.txt"

    save_tree(folder_to_scan, output_txt)
    print(f"Tree-style folder structure saved to {output_txt}")
