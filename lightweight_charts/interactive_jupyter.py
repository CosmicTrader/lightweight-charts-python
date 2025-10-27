"""
Interactive JupyterChart that can communicate back to Python using window.postMessage
"""

import json
import html as html_module
from IPython.display import HTML, display, Javascript
import uuid
from .widgets import StaticLWC
from . import abstract


class InteractiveJupyterChart(StaticLWC):
    """
    A JupyterChart variant that can retrieve data from the chart using postMessage.
    """

    def __init__(
        self,
        width: int = 800,
        height=350,
        inner_width=1,
        inner_height=1,
        scale_candles_only: bool = False,
        toolbox: bool = False,
    ):
        super().__init__(
            width, height, inner_width, inner_height, scale_candles_only, toolbox, False
        )

        self._message_id = f"chart_{uuid.uuid4().hex[:8]}"
        self._latest_drawings = None

        self.run_script(
            f"""
            for (var i = 0; i < document.getElementsByClassName("tv-lightweight-charts").length; i++) {{
                    var element = document.getElementsByClassName("tv-lightweight-charts")[i];
                    element.style.overflow = "visible"
                }}
            document.getElementById('container').style.overflow = 'hidden'
            document.getElementById('container').style.borderRadius = '10px'
            document.getElementById('container').style.width = '{self.width}px'
            document.getElementById('container').style.height = '100%'
            """
        )
        self.run_script(f"{self.id}.chart.resize({width}, {height})")

        # Add postMessage handler in the iframe
        self.run_script(
            f"""
            window.sendDrawingsToParent = function() {{
                if ({self.id}.toolBox) {{
                    const drawings = {self.id}.toolBox.getDrawingsData();
                    window.parent.postMessage({{
                        type: 'drawings',
                        chartId: '{self._message_id}',
                        data: drawings
                    }}, '*');
                }}
            }};
            
            // Auto-send drawings after each drawing is completed
            if ({self.id}.toolBox) {{
                const originalSave = {self.id}.toolBox.saveDrawings;
                {self.id}.toolBox.saveDrawings = function() {{
                    originalSave.call({self.id}.toolBox);
                    window.sendDrawingsToParent();
                }};
            }}
        """
        )

    def _load(self):
        if HTML is None:
            raise ModuleNotFoundError(
                "IPython.display.HTML was not found, and must be installed."
            )

        html_code = html_module.escape(f"{self._html}</script></body></html>")
        iframe = f'<iframe id="chart-iframe-{self._message_id}" width="{self.width}" height="{self.height}" frameBorder="0" srcdoc="{html_code}"></iframe>'

        # Add message listener in parent window
        listener_script = f"""
        <script>
            window.chartDrawings_{self._message_id} = [];
            window.addEventListener('message', function(event) {{
                if (event.data.type === 'drawings' && event.data.chartId === '{self._message_id}') {{
                    window.chartDrawings_{self._message_id} = event.data.data;
                    console.log('Received drawings:', event.data.data);
                }}
            }});
        </script>
        """

        display(HTML(listener_script + iframe))

    def get_drawings(self):
        """
        Get current drawings from the chart.
        This uses JavaScript injection to retrieve data from the iframe.

        Returns:
            List of drawings with their data
        """
        # Trigger sending drawings
        display(
            Javascript(
                f"""
            const iframe = document.getElementById('chart-iframe-{self._message_id}');
            if (iframe && iframe.contentWindow) {{
                iframe.contentWindow.sendDrawingsToParent();
            }}
        """
            )
        )

        # Get the drawings from the global variable
        result_js = Javascript(
            f"""
            IPython.notebook.kernel.execute(
                'chart._latest_drawings = ' + JSON.stringify(window.chartDrawings_{self._message_id})
            );
        """
        )
        display(result_js)

        return self._latest_drawings
