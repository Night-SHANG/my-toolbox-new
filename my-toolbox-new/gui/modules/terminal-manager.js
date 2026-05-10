/**
 * 终端管理模块 - 处理终端输出显示
 */
export class TerminalManager {
    constructor(app) {
        this.app = app;
    }
}

// 更新终端输出的函数（由后端调用）
// 注意：这是全局函数，需要在全局作用域定义
window.updateTerminal = function(content) {
    const terminalOutput = document.getElementById('terminal-output');
    terminalOutput.innerHTML += content;
    // 自动滚动到底部
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
};