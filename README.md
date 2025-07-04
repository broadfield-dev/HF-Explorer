# Huggingface File Explorer Component
![image](splash.png)


A custom Gradio component that provides a powerful file explorer and environment inspector. It can be easily embedded into any Gradio application to allow users to:

- Navigate the local file system (Linux).
- View and inspect file contents.
- Check installed Python dependencies (`pip freeze`).
- View system disk usage (`df -h`).

This component is particularly useful for debugging and inspecting environments in services like Hugging Face Spaces.

## ❗ Warning 
This will expose your environmental keys and entire file system to the user, so remember to set your Huggingface Space to Private.


## Installation

You can install this component directly from GitHub:

```bash
pip install git+https://github.com/broadfield-dev/hf-explorer.git
```

## Usage

Using the `FileExplorer` is as simple as importing it and instantiating it within a `gr.Blocks` app.

```python
import gradio as gr
from hf_explorer.file_explorer import FileExplorer

with gr.Blocks() as demo:
    gr.Markdown("# My Awesome Application")
    gr.Markdown("Below is an instance of the `FileExplorer` component, which can be embedded in any Gradio app.")
    
    # Just instantiate the component class!
    FileExplorer(root_path = f"/home/user", DEMO=True)
    
    gr.Markdown("---")
    gr.Textbox(label="You can have other Gradio components here too!")

if __name__ == "__main__":
    demo.launch()

```

## Customization

You can customize the initial paths when creating an instance of the `FileExplorer`:

```python
FileExplorer(
    root_path="/",                 # The top-level directory user can access
    app_path="/app",               # The "Home" button destination
    glob="*.py"                    # Only show python files
)
```

## System Dependencies

This component uses the following command-line tools for full functionality. They are typically pre-installed on Linux and macOS systems (like Hugging Face Spaces).

- `file`: To determine the MIME type of a file and avoid displaying binary content.
- `df`: To display disk usage information.

The component will still function without them, but with reduced capabilities.
