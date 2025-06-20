import gradio as gr
import os
import pandas as pd
from pathlib import Path
import datetime
import subprocess

# --- Helper Functions ---

# Function to get directory contents and format them for the DataFrame
def get_directory_contents(path_str):
    try:
        path = Path(path_str)
        if not path.is_dir():
            return pd.DataFrame(), f"Error: '{path_str}' is not a valid directory."

        items = []
        for item in path.iterdir():
            try:
                stat = item.stat()
                is_dir = item.is_dir()
                items.append({
                    "Name": item.name,
                    "Type": "📁 Folder" if is_dir else "📄 File",
                    "Size (bytes)": stat.st_size if not is_dir else "",
                    "Modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    "Permissions": oct(stat.st_mode)[-3:],
                    "Full Path": str(item.resolve())
                })
            except Exception:
                # Handle cases like broken symlinks
                items.append({ "Name": item.name, "Type": "❓ Unknown", "Size (bytes)": "N/A", "Modified": "N/A", "Permissions": "N/A", "Full Path": str(item)})

        # Sort by type (folders first) and then by name
        df = pd.DataFrame(items)
        if not df.empty:
            df = df.sort_values(by=['Type', 'Name'], ascending=[False, True])
        return df, f"Currently viewing: {path.resolve()}"
    except Exception as e:
        return pd.DataFrame(), f"Error: {str(e)}"

# Function to read the content of a file
def get_file_content(filepath):
    try:
        path = Path(filepath)
        if path.is_dir():
            return "# This is a directory. Please select a file to view its content.", ""
        # Heuristic to check if it's a binary file
        if "text" not in str(subprocess.run(['file', '--mime-type', '-b', filepath], capture_output=True, text=True).stdout):
             return f"# File '{path.name}' appears to be a binary file.\n# Cannot display content.", filepath
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content, filepath
    except Exception as e:
        return f"# Error reading file: {str(e)}", filepath

# Function to run pip freeze
def get_pip_freeze():
    try:
        result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"Error running 'pip freeze': {str(e)}"

# Function to get disk usage
def get_disk_usage():
    try:
        result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
        return result.stdout
    except Exception as e:
        return f"Error running 'df -h': {str(e)}"
        
# --- Gradio UI ---

with gr.Blocks(theme=gr.themes.Soft(), title="Space Inspector") as demo:
    gr.Markdown("# 🚀 Space Inspector Dashboard")
    gr.Markdown("An environment explorer for your Hugging Face Space. Inspect the filesystem, installed dependencies, and system info.")

    # State to keep track of the current directory
    current_dir_state = gr.State(value="/")

    with gr.Tabs():
        # --- TAB 1: FILE EXPLORER ---
        with gr.TabItem("📂 File Explorer"):
            with gr.Row():
                # Directory Navigation
                with gr.Column(scale=1, min_width=250):
                    gr.Markdown("### Navigation")
                    up_button = gr.Button("⬆️ Go Up")
                    home_button = gr.Button("🏠 Go to App Home (/code)")
                    root_button = gr.Button("̸ Go to Root (/)")
                    
                    gr.Markdown("### Go to Path:")
                    path_input = gr.Textbox(label="Enter path and press Enter", value="/", interactive=True)

                # File/Folder Listing
                with gr.Column(scale=3):
                    current_path_display = gr.Label(label="Current Directory")
                    file_list_df = gr.DataFrame(
                        headers=["Name", "Type", "Size (bytes)", "Modified", "Permissions"],
                        datatype=["str", "str", "str", "str", "str"],
                        interactive=True,
                        row_count=(15, "dynamic")
                    )
            
            # File Content Viewer
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### File Content Viewer")
                    selected_file_path = gr.Textbox(label="Selected File Path", interactive=False)
                    file_content_display = gr.Code(label="Content", language="python", lines=20, interactive=False)
        
        # --- TAB 2: DEPENDENCY INSPECTOR ---
        with gr.TabItem("🐍 Dependency Inspector") as dep_tab:
            gr.Markdown("View all installed Python packages in the environment (`pip freeze`).")
            refresh_pip_button = gr.Button("Refresh Pip List")
            pip_list_display = gr.Code(label="pip freeze output", language="shell", lines=30)
            
        # --- TAB 3: SYSTEM INFO ---
        with gr.TabItem("ℹ️ System Info") as sys_tab:
            gr.Markdown("View system information like disk usage.")
            refresh_sysinfo_button = gr.Button("Refresh System Info")
            sysinfo_display = gr.Code(label="df -h (Disk Usage)", language="shell", lines=20)


    # --- Event Handlers ---

    # Function to update the file list display
    def update_file_list(path_str):
        df, label = get_directory_contents(path_str)
        return df, label, path_str
    
    # When the app loads or path changes
    demo.load(fn=update_file_list, inputs=[current_dir_state], outputs=[file_list_df, current_path_display, current_dir_state])
    path_input.submit(fn=update_file_list, inputs=[path_input], outputs=[file_list_df, current_path_display, current_dir_state])

    # When a row in the dataframe is selected (either a file or folder)
    def handle_row_select(evt: gr.SelectData, df: pd.DataFrame, current_dir: str):
        if evt.index is None:
            return gr.update(), gr.update(), gr.update()
            
        selected_row = df.iloc[evt.index[0]]
        item_path = Path(current_dir) / selected_row["Name"]

        if selected_row["Type"] == "📁 Folder":
            # If it's a directory, update the file list to show its contents
            new_df, new_label = get_directory_contents(str(item_path))
            return new_df, new_label, "# This is a directory. Please select a file to view its content.", "", str(item_path)
        else:
            # If it's a file, get its content
            content, filepath = get_file_content(str(item_path))
            return gr.update(), gr.update(), content, filepath, gr.update()

    file_list_df.select(
        handle_row_select,
        [file_list_df, current_dir_state],
        [file_list_df, current_path_display, file_content_display, selected_file_path, current_dir_state]
    )

    # Navigation buttons
    def go_up(current_dir):
        path = Path(current_dir).parent
        return update_file_list(str(path))

    up_button.click(go_up, [current_dir_state], [file_list_df, current_path_display, current_dir_state])
    home_button.click(lambda: update_file_list("/code"), [], [file_list_df, current_path_display, current_dir_state])
    root_button.click(lambda: update_file_list("/"), [], [file_list_df, current_path_display, current_dir_state])
    
    # Handlers for other tabs
    refresh_pip_button.click(get_pip_freeze, [], pip_list_display)
    refresh_sysinfo_button.click(get_disk_usage, [], sysinfo_display)
    
    # Load data on tab selection for convenience
    dep_tab.select(get_pip_freeze, [], pip_list_display)
    dep_tab.select(get_disk_usage, [], sysinfo_display)


if __name__ == "__main__":
    demo.launch()
