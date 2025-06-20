import gradio as gr
import os
import pandas as pd
from pathlib import Path
import datetime
import subprocess

class FileExplorer(gr.Blocks):
    """
    A Gradio component that acts as a comprehensive file explorer and environment inspector.
    It allows users to navigate the local filesystem, view file contents, and inspect system
    and dependency information. It is designed to be easily embedded into any Gradio application.
    """
    def __init__(self, root_path: str = "/", app_path: str = f"{os.getcwd()}", glob: str = "*", DEMO=False, **kwargs):
        """
        Parameters:
            root_path (str): The default root directory for the explorer (e.g., "/").
            app_path (str): The path to the "home" directory of the application.
            glob (str): A glob pattern to filter the files shown. Defaults to "*" (all files).
            **kwargs: Additional keyword arguments to pass to the gr.Blocks constructor.
        """
        super().__init__(**kwargs)
        self.root_path = root_path
        self.app_path = app_path
        self.glob_pattern = glob

        with self:
            with gr.Accordion("HF File Explorer"):
                gr.Markdown("# 🚀 Space Inspector Dashboard")
                gr.Markdown("An environment explorer for your Hugging Face Space. Inspect the filesystem, installed dependencies, and system info.")
                gr.Markdown("""## ❗ Warning
                        This will expose your environmental variables and entire file system to the user, so remember to set your Huggingface Space to Private.""")
                self.current_dir_state = gr.State(value=self.root_path)
                with gr.Tabs():
                    with gr.TabItem("📂 File Explorer"):
                        with gr.Row():
                            with gr.Column(scale=1, min_width=250):
                                gr.Markdown("### Navigation")
                                self.up_button = gr.Button("⬆️ Go Up")
                                self.home_button = gr.Button(f"🏠 Go to App Home ({self.app_path})")
                                self.root_button = gr.Button(f"̸ Go to Root ({self.root_path})")
                                gr.Markdown("### Go to Path:", visible = True if DEMO == False else False)
                                self.path_input = gr.Textbox(label="Enter path and press Enter", value=self.root_path, interactive=True, visible = True if DEMO == False else False)
                            with gr.Column(scale=3):
                                self.current_path_display = gr.Label(label="Current Directory")
                                self.file_list_df = gr.DataFrame(headers=["Name", "Type", "Size (bytes)", "Modified", "Permissions"], datatype=["str", "str", "str", "str", "str"], interactive=True, row_count=(15, "dynamic"))
                        with gr.Row():
                            with gr.Column():
                                gr.Markdown("### File Content Viewer")
                                self.selected_file_path = gr.Textbox(label="Selected File Path", interactive=False)
                                self.file_content_display = gr.Code(label="Content", language="python", lines=20, interactive=False)
                    
                    with gr.TabItem("🐍 Dependency Inspector"):
                        gr.Markdown("View all installed Python packages in the environment (`pip freeze`).")
                        self.refresh_pip_button = gr.Button("Refresh Pip List")
                        self.pip_list_display = gr.Code(label="pip freeze output", language="shell", lines=30)
                    
                    with gr.TabItem("🌿 Environment Variables"):
                        gr.Markdown("View all environment variables available to the application (`os.environ`).")
                        self.refresh_env_button = gr.Button("Refresh Environment Variables")
                        self.env_vars_display = gr.Code(label="Environment Variables", language="shell", lines=30)
    
                    with gr.TabItem("ℹ️ System Info"):
                        gr.Markdown("View system information like disk usage.")
                        self.refresh_sysinfo_button = gr.Button("Refresh System Info")
                        self.sysinfo_display = gr.Code(label="df -h (Disk Usage)", language="shell", lines=20)
                
            self.load(fn=self.update_file_list, inputs=[self.current_dir_state], outputs=[self.file_list_df, self.current_path_display, self.current_dir_state])
            self._attach_event_handlers()

    def _attach_event_handlers(self):
        """Attaches all the event handlers to the UI components."""
        self.path_input.submit(fn=self.update_file_list, inputs=[self.path_input], outputs=[self.file_list_df, self.current_path_display, self.current_dir_state])
        self.file_list_df.select(self.handle_row_select, [self.file_list_df, self.current_dir_state], [self.file_list_df, self.current_path_display, self.file_content_display, self.selected_file_path, self.current_dir_state])
        self.up_button.click(self.go_up, [self.current_dir_state], [self.file_list_df, self.current_path_display, self.current_dir_state])
        self.home_button.click(lambda: self.update_file_list(self.app_path), [], [self.file_list_df, self.current_path_display, self.current_dir_state])
        self.root_button.click(lambda: self.update_file_list(self.root_path), [], [self.file_list_df, self.current_path_display, self.current_dir_state])
        
        self.refresh_pip_button.click(self.get_pip_freeze, [], self.pip_list_display)
        self.refresh_env_button.click(self.get_environment_variables, [], self.env_vars_display)
        self.refresh_sysinfo_button.click(self.get_disk_usage, [], self.sysinfo_display)
        
        self.pip_list_display.attach_load_event(self.get_pip_freeze, [])
        self.env_vars_display.attach_load_event(self.get_environment_variables, [])
        self.sysinfo_display.attach_load_event(self.get_disk_usage, [])

    def get_directory_contents(self, path_str):
        try:
            path = Path(path_str).resolve()
            if not path.is_dir():
                return pd.DataFrame(), f"Error: '{path_str}' is not a valid directory."
            items = []
            for item in sorted(path.glob(self.glob_pattern), key=lambda p: (p.is_file(), p.name.lower())):
                try:
                    stat = item.stat()
                    is_dir = item.is_dir()
                    items.append({"Name": item.name, "Type": "📁 Folder" if is_dir else "📄 File", "Size (bytes)": stat.st_size if not is_dir else "", "Modified": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'), "Permissions": oct(stat.st_mode)[-3:], "Full Path": str(item.resolve())})
                except Exception:
                    items.append({"Name": item.name, "Type": "❓ Unknown", "Size (bytes)": "N/A", "Modified": "N/A", "Permissions": "N/A", "Full Path": str(item)})
            df = pd.DataFrame(items)
            return df, f"Currently viewing: {path}"
        except Exception as e:
            return pd.DataFrame(), f"Error: {str(e)}"

    def get_file_content(self, filepath):
        try:
            path = Path(filepath)
            if path.is_dir():
                return "# This is a directory. Please select a file to view its content.", ""
            try:
                mime_type = subprocess.run(['file', '--mime-type', '-b', str(path)], capture_output=True, text=True, check=True).stdout.strip()
                if "text" not in mime_type and "json" not in mime_type:
                    return f"# File '{path.name}' appears to be a binary file ({mime_type}).\n# Cannot display content.", filepath
            except (FileNotFoundError, subprocess.CalledProcessError):
                pass
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1024 * 1024)
            return content, filepath
        except Exception as e:
            return f"# Error reading file: {str(e)}", filepath
            
    def get_pip_freeze(self):
        try:
            result = subprocess.run(['pip', 'freeze'], capture_output=True, text=True, check=True)
            return result.stdout
        except Exception as e:
            return f"Error running 'pip freeze': {str(e)}"
    
    def get_environment_variables(self):
        """Retrieves and formats all environment variables."""
        try:
            vars_list = [f"{key}={value}" for key, value in sorted(os.environ.items())]
            return "\n".join(vars_list)
        except Exception as e:
            return f"Error retrieving environment variables: {str(e)}"

    def get_disk_usage(self):
        try:
            result = subprocess.run(['df', '-h'], capture_output=True, text=True, check=True)
            return result.stdout
        except Exception as e:
            return f"Error running 'df -h': {str(e)}"

    def update_file_list(self, path_str):
        df, label = self.get_directory_contents(path_str)
        return df, label, path_str

    def handle_row_select(self, evt: gr.SelectData, df: pd.DataFrame, current_dir: str):
        if evt.index is None:
            return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        selected_row = df.iloc[evt.index[0]]
        item_path_str = selected_row["Full Path"]
        if selected_row["Type"] == "📁 Folder":
            df, label = self.get_directory_contents(item_path_str)
            content_update = "# This is a directory. Please select a file to view its content."
            return df, label, content_update, "", item_path_str
        else:
            content, filepath = self.get_file_content(item_path_str)
            return gr.update(), gr.update(), content, filepath, gr.update()

    def go_up(self, current_dir):
        if not current_dir == self.root_path:
            path = Path(current_dir).parent
            return self.update_file_list(str(path))
        else:
            return self.update_file_list(str(current_dir))
