*** Settings ***
Resource    keywords/common.resource
Suite Setup    Create Authenticated Session Python

*** Variables ***
${BASE_URL}    http://localhost:8000

*** Test Cases ***

# Authentication

Login With Valid Credentials Returns 200
    ${body}=    Create Dictionary    username=admin    password=admin123
    ${response}=    POST On Session    python_api    /auth/login    json=${body}    expected_status=200
    Should Not Be Empty    ${response.json()["access_token"]}

Login With Invalid Credentials Return 401
    ${body}=    Create Dictionary    username=wrong    password=wrong123
    ${response}=    POST On Session    python_api    /auth/login    json=${body}    expected_status=401

Login With Empty Credentials Return 401
    ${body}=    Create Dictionary    username=    password=
    ${response}=    POST On Session    python_api    /auth/login    json=${body}    expected_status=401

# Task testing
Get Tasks Without Auth Should Return 401
    # BUG 1 missing auth
    Create Session    no_auth    ${BASE_URL}
    ${response}=    GET On Session    no_auth    /tasks    expected_status=401

Get Tasks With Auth returns 200
    #BUg 2 returns 200 insted of 201
    ${headers}=    Get Python Headers
    ${response}=    GET On Session    python_api    /tasks    headers=${headers}    expected_status=200

Create Task Should Return 201 But Returns 200
    ${headers}=    Get Python Headers
    ${body}=    Create Dictionary    title=Testing Task    priority=${1}
    ${resposne}=    POST On Session    python_api    /tasks    json=${body}    headers=${headers}    expected_status=201

Create Task With Null Title Should Return 400
    #Bug 3 accepts null titles
    ${headers}=    Get Python Headers
    ${body}=    Create Dictionary    priority=${1}
    ${resposne}=    POST On Session    python_api    /tasks    json=${body}    headers=${headers}    expected_status=422

Get Nonexists Task Returns 404
    #Bug 4 returns 200 instead of 404
    ${headers}=    Get Python Headers
    ${respone}=    GET On Session    python_api    /tasks/99999    headers=${headers}    expected_status=404

Delete Task Returns 204
    # BUG B5 returns 200 instead of 204
    ${headers}=    Get Python Headers
    ${body}=    Create Dictionary    title=Task To Delete    priority=${1}
    ${create}=    POST On Session    python_api    /tasks    json=${body}    headers=${headers}
    ${task_id}=    Set Variable    ${create.json()['id']}
    ${response}=    DELETE On Session    python_api    /tasks/${task_id}    headers=${headers}    expected_status=204