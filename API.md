# `202.117.24.3:8088` Library Reservation System (Intranet) API Documentation

## Get Space List

- **Endpoint**: `GET /qseatui`
- **Request Parameters**:

  | Parameter | Type   | Required | Description                          |
  |-----------|--------|----------|--------------------------------------|
  | `sp`      | string | Yes      | Area identifier, e.g. `xingqing2floor` |

- **Example Request**:
  ```
  GET http://<host>:<port>/qseatui?sp=xingqing2floor
  ```

- **Response Format** (JSON):
  ```json
  {
    "north2": {...},
    "south2": {...},
    "spacecancel": {...},
    "": {...}
  }
  ```

- **Response Description**:

  | Field         | Type   | Description                                       |
  |---------------|--------|---------------------------------------------------|
  | Space ID      | object | Detailed information of a valid space             |
  | `""`          | object | Invalid space, should be ignored                  |
  | `spacecancel` | object | Canceled space, should be ignored                 |

---

## Get Seat Status

- **Endpoint**: `GET /qseatuist`
- **Request Parameters**:

  | Parameter | Type   | Required | Description                     |
  |-----------|--------|----------|---------------------------------|
  | `sp`      | string | Yes      | Space ID, e.g. `eastnorthda`    |

- **Example Request**:
  ```
  GET http://<host>:<port>/qseatuist?sp=eastnorthda
  ```

- **Response Format** (JSON):
  ```json
  {
    "P001": [1,2,3,4,5],
    "P002": [1,2,3,4,5],
    "cancel": [...],
    "": [...]
  }
  ```

  - `P001`, `P002` are seat IDs.
  - The seat status list contains:
    - The first four numbers: coordinates for rendering a rectangle in the frontend
    - The fifth number: seat status code:
      - `0`: Reserved seat
      - `1`: In use
      - `2`: Available
      - `3`: Temporarily left

---

## Get User Reservation Status

- **Endpoint**: `GET /quserinfo`
- **Request Parameters**:

  | Parameter  | Type   | Required | Description                  |
  |------------|--------|----------|------------------------------|
  | `cardno`   | string | Yes      | User's library card number   |

- **Example Request**:
  ```
  GET http://<host>:<port>/quserinfo?cardno=2020123456
  ```

- **Response Format** (JSON):
  ```json
  {
    "status": "0",        
    "message": // Unicode string with typical outputs such as:
               // - 未能成功读取卡号
               // - 未能找到读者 XXXXXXXX 今日的活跃申请，请重新预约
               // - 读者 XXXXXXXXX 今日申请SPACE_ID SEAT_ID,状态已入馆
  }
  ```

- **Response Description**:

  | Field     | Type   | Description                                    |
  |-----------|--------|------------------------------------------------|
  | `status`  | string | `"-1"`: No reservation; `"1"`: Reservation exists |
  | `message` | string | See comments above for typical message patterns |

---

## System Entry Page

- **Endpoint**: `GET /seatuieast/#`
- **Request Parameters**: None

- **Example Request**:
  ```
  GET http://<host>:<port>/seatuieast/#
  ```

- **Response**:
  Returns an HTML page that includes the title or keyword `"西安交通大学图书馆图书预约系统"`.

---

## Submit Reservation Request

- **Endpoint**: `POST /seatuieast/#`
- **Request Parameters** (Form Data):

  | Parameter | Type   | Required | Description                       |
  |-----------|--------|----------|-----------------------------------|
  | `No`      | string | Yes      | User’s library card number        |
  | `kid`     | string | Yes      | Seat ID, e.g. `P004`              |
  | `sp`      | string | Yes      | Space ID, e.g. `eastnorthda`      |

- **Example Request**:
  ```http
  POST /seatuieast/# HTTP/1.1
  Content-Type: application/x-www-form-urlencoded

  No=2020123456&kid=P004&sp=eastnorthda
  ```

- **Response Description**:
  Returns an HTML page (same as `/seatuieast/#`) with an added prompt message indicating the result of the reservation. The message includes one of the following keywords:
  - `"Success"` or `"Changed seat"`: Reservation successful
  - `"Already reserved"`: Seat is already taken

---

## Appendix: API Summary

| Function                  | Method | Path               | Description                          |
|---------------------------|--------|--------------------|--------------------------------------|
| Area → Space Query        | GET    | `/qseatui`         | Get a list of space IDs under a specific area |
| Space → Seat Status Query | GET    | `/qseatuist`       | Get all seat statuses under a specific space  |
| User Reservation Status   | GET    | `/quserinfo`       | Check the current user’s reservation status   |
| System Page Validation    | GET    | `/seatuieast/#`    | Verify if the system page is accessible       |
| Submit Reservation        | POST   | `/seatuieast/#`    | Submit a seat reservation request            |
