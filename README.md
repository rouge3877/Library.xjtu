# Library.xjtu

> 每次使用前先承认，不是你成功 hack 了学校的系统，而是网管这一次放过了你~

Repo由两部分构成，分别是 Pin 住图书馆的座位以及预约图书馆的空间。

## 🪑 Book Seats

### Prerequisite: 获取 `cardno`
每个人的校园卡中都包含一个 `cardno`。当你在图书馆的机器上刷卡选座时，读卡机会读取这串数字并提交给系统。所以，也就是当你选择好座位并刷卡确认后，系统会发送一个 HTTP 请求，而你的 `cardno` 就藏在里面。
> PS: 这个系统是：[http://202.117.24.3:8088/seatuieast/#](http://202.117.24.3:8088/seatuieast/#)，而且XJTU内网内就能访问

因此你可以：
1. 在图书馆内部的选座机上操作预约。
2. 打开浏览器的开发者工具 (`F12` -> `Network`)。
3. 完成一次顺利的预约。
4. 在 Network 面板中找到名为 `seatuieast` 的请求 (如下图)。
   <img width="1022" height="202" alt="image" src="https://github.com/user-attachments/assets/2a80a90d-a982-479c-aa3f-eee377171a01" />
5. 点击该请求的 **Payload** 选项卡，找到 `no` 这一项对应的数字：
   <img width="714" height="145" alt="image" src="https://github.com/user-attachments/assets/9e72ca54-623a-4b7e-b7e9-852ea2594172" />
   记下这串数字，这就是你的 `cardno`。

### 预约座位

有了 `cardno`，你就可以利用本项目来预约座位了，运行 `python src/seat/seat_reserve.py --help` 查看具体参数与使用。

> 这其实本质上就是“强行霸占”——因为它完全模拟了你在图书馆选座机上的操作，也即是系统：[http://202.117.24.3:8088/seatuieast/#](http://202.117.24.3:8088/seatuieast/#)。由于系统没有任何高级的认证机制，我们只需要构造一个包含你 `cardno` 的 payload，就能直接把座位 Pin 住。
> Repo中的 `src/seat/seat_reserve.py` 正是利用了这一机制，当然脚本在 `cardno` 之外也需要别的参数，但是通过简单读一下[http://202.117.24.3:8088/seatuieast/#](http://202.117.24.3:8088/seatuieast/#)中的code就能明白。

当然，如果你觉得看code，用python太麻烦也没关系。这里提供一种极为简易且优雅的交互方式：

<script src="[https://gist.github.com/rouge3877/6a75b4e8e2e707400ce4b952cd48f9ff.js](https://gist.github.com/rouge3877/6a75b4e8e2e707400ce4b952cd48f9ff.js)"></script>
  
1. 安装 **Tampermonkey** (油猴)、**Greasemonkey** 或其他类似的浏览器插件。
2. 将上面的脚本添加进去。
3. 确保你处于校园网环境（XJTU VPN 或你喜欢的任何进入内网的姿势）。
4. 访问：[http://202.117.24.3:8088/seatuieast/#](http://202.117.24.3:8088/seatuieast/#)
  此时，你会发现预约系统上方多出了一个输入框：
  <img width="1642" height="528" alt="image" src="https://github.com/user-attachments/assets/e85aa3ae-e120-41ed-a347-031324ebb07a" />
  在这里输入我们要到的 `cardno`，然后点击 **Manual Submit** (或者直接回车)，效果就等同于你在图书馆机器上刷了一下卡。
  回忆图书馆选座机的操作——现在，你就可以用自己的电脑/手机/平板/手表，随时随地进行 **预约/换座/中途离馆/回馆签到** 了。


---

## 🏢 Reserve Space

这一块就没有危险了，本质就是在老老实实地预约空间而已~

你可以crontab等定时约每周3的某会议室，如果你每周要参加一个remote Group Meeting
