import gradio as gr
from gradio_file_explorer import FileExplorer # Import the component

with gr.Blocks() as demo:
    gr.Markdown("# My Awesome Application")
    gr.Markdown("Below is an instance of the `FileExplorer` component, which can be embedded in any Gradio app.")
    
    # Just instantiate the component class!
    # You can customize it, e.g., FileExplorer(root_path="/etc")
    FileExplorer()
    
    gr.Markdown("---")
    gr.Textbox(label="You can have other Gradio components here too!")

if __name__ == "__main__":
    demo.launch()
