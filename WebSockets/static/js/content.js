// Support TLS-specific URLs, when appropriate.
if (window.location.protocol == "https:") {
  var ws_scheme = "wss://";
} else {
  var ws_scheme = "ws://"
};


var inbox = new ReconnectingWebSocket(ws_scheme + location.host + "/receive");
var outbox = new ReconnectingWebSocket(ws_scheme + location.host + "/submit");

var id = Math.random().toString(36).slice(2);
var avatar_img = '';

var current_time = getNowFormatDate();
// console.log(current_time);


// 用于指定收到服务器数据后的回调函数
inbox.onmessage = function(message) {
    // console.log(message);
    let data = JSON.parse(message.data);
    console.log(data);

    //消息
    if(data['message'] !== undefined) {
        // 如果不是当前用户id，即为接收到的消息，就显示在左侧
        if(data['message']['id'] !== id){
            $("#chat-text").append(data['message']['content']);
            $("#chat-text").stop().animate({
                scrollTop: $('#chat-text')[0].scrollHeight
            }, 800);

            $('body').barrager(data['barrage']);
        }
    } else if(data['message'] === undefined){
        //头像（用户还没发消息时，后台随机选取的头像）
        avatar_img = data['avatar'];
        console.log(avatar_img);

    }

};
// ws.onclose: 用于指定服务器端连接关闭后的回调函数
inbox.onclose = function(){
    console.log('inbox closed');
    this.inbox = new WebSocket(inbox.url);

};

outbox.onclose = function(event){
    console.log('outbox closed');
    console.log(event.data);
    this.outbox = new WebSocket(outbox.url);
};

// 获取表单提交的信息
$("#input-form").on("submit", function(event) {
    event.preventDefault();
    if (checkNull()  === true){
        let handle = $("#input-handle")[0].value;
        let text   = $("#input-text")[0].value;

        // 用户自己发出的消息直接从前台获取，并显示在右侧
        $("#chat-text").append(" <img class='message-avatar' alt=''> <div class='message'> <a class='message-author' href='#'> " + handle+ " </a> <span class='message-date'> " + current_time + "</span> <pre class='message-content'>" + text + "</pre> </div>");
        $(".message-avatar").attr('src', 'static/img/' + avatar_img);


        // 添加弹幕
        let item = {
            'img':'static/img/' + avatar_img,
            'info':text,
            'close':true,
            'speed':10,
            'color':'#fff',
            'old_ie_color':'#000000'
        };

        $('body').barrager(item);

        // console.log(id);
        outbox.send(JSON.stringify({ handle: handle, text: text, id: id, avatar: avatar_img, item:item}));

        $("#input-text")[0].value = "";


    }
});

// 按回车触发按钮事件
$("#input-text").keydown(function(event){
    if (event.shiftKey && event.keyCode === 13){
        event.preventDefault();
        $("#submit_btn").click();
    }
});

// 判断表单是否为空
function checkNull() {
     var num=0;
     var str="";
     $("textarea[type$='text']").each(function(n){
          if($(this).val().trim()==="")
          {
               num++;
               str+="发送信息不能为空！\r\n";
          }
     });
     $("input[type$='text']").each(function(n){
          if($(this).val()==="")
          {
               num++;
               str+="用户名不能为空！\r\n";
          }
     });
     if(num>0)
     {
          alert(str);
          return false;
     }
     else
     {
          return true;
     }
}

//前台页面获取当前时间
function getNowFormatDate() {
    var date = new Date();
    var seperator1 = "-";
    var seperator2 = ":";
    var month = date.getMonth() + 1;
    var strDate = date.getDate();
    if (month >= 1 && month <= 9) {
        month = "0" + month;
    }
    if (strDate >= 0 && strDate <= 9) {
        strDate = "0" + strDate;
    }
    var currentdate = date.getFullYear() + seperator1 + month + seperator1 + strDate
            + " " + date.getHours() + seperator2 + date.getMinutes()
            + seperator2 + date.getSeconds();
console.log(currentdate);
    return currentdate;
}
