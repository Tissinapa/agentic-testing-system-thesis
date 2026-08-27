*** Settings ***
Resource    keywords/common.resource
Suite Setup    Create Authenticated Session Java

*** Variables ***
${BASE_URL}    http://localhost:8080

*** Test Cases ***
#Authentication

Login With Valid Credentials Returns 200
    ${body}=    Create Dictionary    username=admin    password=passu123salis
    ${response}=    POST On Session    java_api    /auth/login    json=${body}    expected_status=200
    Should Not Be Empty    ${response.json()["accessToken"]}

Login With Invalid Credentials Return 401
    ${body}=    Create Dictionary    username=wrong    password=wrong123
    ${response}=    POST On Session    java_api    /auth/login    json=${body}    expected_status=401

Login With Empty Credentials Return 400
    ${body}=    Create Dictionary    username=    password=
    ${response}=    POST On Session    java_api    /auth/login    json=${body}    expected_status=400

Get Tasks Without Auth Should Return 401
    # BUG 1 missing auth
    Create Session    no_auth    ${BASE_URL}
    ${response}=    GET On Session    no_auth    /tasks    expected_status=401

Get Tasks With Auth returns 200
    #BUg 2 returns 200 insted of 201
    ${headers}=    Get Java Headers
    ${response}=    GET On Session    java_api    /tasks    headers=${headers}    expected_status=200

Create Task Returns 201
    ${headers}=    Get Java Headers
    ${body}=    Create Dictionary    title=Testing Task    priority=${1}
    ${resposne}=    POST On Session    java_api    /tasks    json=${body}    headers=${headers}    expected_status=201

Create Task With Null Title Should Return 400
    #Bug 3 accepts null titles
    ${headers}=    Get Java Headers
    ${body}=    Create Dictionary    priority=${1}
    ${resposne}=    POST On Session    java_api    /tasks    json=${body}    headers=${headers}    expected_status=500

Get Nonexists Task Returns 404
    #Bug 4 returns 200 instead of 404
    ${headers}=    Get Java Headers
    ${respone}=    GET On Session    java_api    /tasks/9999    headers=${headers}    expected_status=404

Delete Task Returns 204
    # BUG B5 returns 200 instead of 204
    ${headers}=    Get Java Headers
    ${body}=    Create Dictionary    title=Task To Delete    priority=${1}
    ${create}=    POST On Session    java_api    /tasks    json=${body}    headers=${headers}
    ${task_id}=    Set Variable    ${create.json()['id']}
    ${response}=    DELETE On Session    java_api    /tasks/${task_id}    headers=${headers}    expected_status=204