
@echo off
:: ���⻷������ű�
echo -------------------------------
echo ���⻷��������
echo ���ܣ�1. �������⻷�����粻���ڣ� 2. �������⻷��
echo -------------------------------

:: 1. ��鲢�������⻷��
if not exist "venv\" (
    echo [1/2] ���ڴ������⻷��...
    python -m venv venv
    echo ���⻷��������ɣ�
) else (
    echo ���⻷���Ѵ��ڣ������������衣
)

:: 2. �������⻷��
echo [2/2] �������⻷��...
call venv\Scripts\activate
if errorlevel 1 (
    echo �������⻷������ʧ�ܣ�
    pause
    exit /b
)

:: ��ʾ�û��ֶ�����
echo -------------------------------
echo ���⻷���Ѽ�����ֶ�ִ�У�
echo   pip install -r requirements.txt
echo ��ֱ�Ӱ�װ����������
echo -------------------------------
cmd /k
