"""
进程运行器 - 负责执行脚本并管理输出
"""
import subprocess
import sys
import shlex
import threading
from pathlib import Path


class ProcessRunner:
    def __init__(self):
        self.process = None
        self.window = None

    def run_script(self, command: list, window):
        """启动脚本子进程，并在后台线程中流式传输其输出。"""
        self.window = window
        try:
            command_display_str = ' '.join(command)
            message = f'<span style="color:yellow;">> {command_display_str}</span><br>'
            self.window.evaluate_js(f'updateTerminal({repr(message)})')

            args = [command[0], '-X', 'utf8', '-u'] + command[1:]

            self.process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
                bufsize=1,
                text=True,
                encoding='utf-8'
            )

            # 创建并启动一个线程来读取输出
            thread = threading.Thread(target=self._stream_output, args=(self.process,))
            thread.daemon = True  # 设置为守护线程，主程序退出时它也会退出
            thread.start()

            return self.process

        except Exception as e:
            error_message = f"<br><span style='color:red;'>无法执行脚本: {str(e)}</span><br>"
            self.window.evaluate_js(f'updateTerminal({repr(error_message)})')
            return None

    def _stream_output(self, process):
        """在线程中运行，读取并转发进程的输出。"""
        while True:
            output_str = process.stdout.readline()
            if not output_str and process.poll() is not None:
                break
            if output_str and self.window:
                try:
                    safe_output = output_str.replace('\\', '\\\\').replace('"', '\\"')
                    if not safe_output.endswith('<br>'):
                        safe_output = safe_output.rstrip('\n\r') + '<br>'
                    self.window.evaluate_js(f'updateTerminal({repr(safe_output)})')
                except Exception as e:
                    # 在窗口关闭后，evaluate_js会失败，此时应终止循环
                    print(f"转发输出到前端时出错 (可能窗口已关闭): {e}")
                    break
        
        return_code = process.wait()
        if self.window:
            if return_code == 0:
                message = '<br><span style="color:lightgreen;">... 脚本执行成功 ...</span><br>'
            else:
                message = f'<br><span style="color:red;">... 脚本执行失败 (退出码: {return_code}) ...</span><br>'
            try:
                self.window.evaluate_js(f'updateTerminal({repr(message)})')
            except Exception as e:
                print(f"发送最终状态到前端时出错 (可能窗口已关闭): {e}")

    def shutdown(self):
        """终止当前正在运行的进程。"""
        if self.process and self.process.poll() is None:
            print("正在终止后台脚本进程...")
            self.process.terminate() # 发送终止信号
            self.process = None
            return True
        return False