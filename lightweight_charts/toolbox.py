import json


class ToolBox:
    def __init__(self, chart):
        self.run_script = chart.run_script
        self.id = chart.id
        self._save_under = None
        self.drawings = {}
        chart.win.handlers[f"save_drawings{self.id}"] = self._save_drawings
        self.run_script(f"{self.id}.createToolBox()")

    def save_drawings_under(self, widget: "Widget"):
        """
        Drawings made on charts will be saved under the widget given. eg `chart.toolbox.save_drawings_under(chart.topbar['symbol'])`.
        """
        self._save_under = widget

    def load_drawings(self, tag: str):
        """
        Loads and displays the drawings on the chart stored under the tag given.
        """
        if not self.drawings.get(tag):
            return
        self.run_script(
            f"if ({self.id}.toolBox) {self.id}.toolBox.loadDrawings({json.dumps(self.drawings[tag])})"
        )

    def import_drawings(self, file_path):
        """
        Imports a list of drawings stored at the given file path.
        """
        with open(file_path, "r") as f:
            json_data = json.load(f)
            self.drawings = json_data

    def export_drawings(self, file_path):
        """
        Exports the current list of drawings to the given file path.
        """
        with open(file_path, "w+") as f:
            json.dump(self.drawings, f, indent=4)

    def _save_drawings(self, drawings):
        if not self._save_under:
            return
        self.drawings[self._save_under.value] = json.loads(drawings)

    def get_drawings(self, tag="current"):
        """
        Returns the drawings stored under the given tag.
        For Jupyter notebooks, first call save_current_drawings() to capture them.
        """
        return self.drawings.get(tag, [])

    def all_drawings(self):
        """
        Returns all drawings from all tags as a dictionary.
        """
        return self.drawings

    def log_drawings_to_console(self):
        """
        Logs all current drawings to the browser console.
        Useful for debugging in Jupyter notebooks - check the browser console (F12).
        """
        self.run_script(f"{self.id}.toolBox?.logDrawingsToConsole()")
        print("Drawings logged to browser console. Open browser console (F12) to view.")

    def download_drawings(self, filename="drawings.json"):
        """
        Triggers a download of all current drawings as a JSON file from the browser.
        This works in Jupyter notebooks and will download the file to your Downloads folder.

        Args:
            filename: Name of the file to download (default: 'drawings.json')
        """
        self.run_script(f'{self.id}.toolBox?.downloadDrawingsAsFile("{filename}")')
        print(f"Download triggered for: {filename}")
        print(f"Check your Downloads folder for the file.")

    def get_live_drawings(self):
        """
        Get current live drawings from the chart (not saved ones).
        This works with QtChart/regular Chart that supports run_script_and_get.

        Returns:
            List of current drawings with their data
        """
        try:
            # Try to get live drawings via JavaScript
            script = f"""
                (function() {{
                    if ({self.id}.toolBox && {self.id}.toolBox._drawingTool) {{
                        const drawings = {self.id}.toolBox._drawingTool.drawings;
                        return drawings.map(d => ({{
                            type: d._type,
                            points: d.points,
                            options: d._options
                        }}));
                    }}
                    return [];
                }})()
            """
            # This requires run_script_and_get which only works with Qt/Wx charts
            if hasattr(self, "run_script_and_get"):
                result = self.run_script_and_get(script)
                return result if result else []
            else:
                # Fallback to saved drawings for static charts
                return self.all_drawings()
        except:
            # Fallback to saved drawings
            return self.all_drawings()
