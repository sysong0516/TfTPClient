# TfTPClient
네트워크 프로그래밍 기말과제 입니다

put기능은 send_wrq()에 wrq송신 및 데이터 송신,ack수신을 포함시켜 구현하였습니다\n
get기능은 if operation==get에 구현하였고 수신받은 packet의 block_number를 확인하여 중복된 데이터블록에 대한 처리를 하였습니다\n
port는 -p를 parameter에 추가하여 설정시 콘솔에 접속한 port의 번호를 출력하도록 하였습니다\n
없는 파일을 서버에 rrq요청시에는 error_code를 확인하여 콘솔에 메시지를 출력하도록 하였습니다
