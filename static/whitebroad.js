

function shuffle(array) {
  var currentIndex = array.length
    , temporaryValue
    , randomIndex
    ;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

function WhitebroadConnection() {
    var ws = new WebSocket("ws://" + window.location.host + "/wb/public"),
        status = $('#status');
        connection = {};


    ws.onopen = function(evt) {
        status.text("open");
        connection.onOpen(evt);
    };
    ws.onclose = function(evt) {
        status.text("closed");
        connection.onClose(evt);
    };
    ws.onmessage = function(evt) {
        status.text("working");
        connection.onMessage(JSON.parse(evt.data), evt);
    };
    ws.onerror = function(evt) {
        status.text("error");
        connection.onError(evt);
    };

    connection.send = function jsonAndSend(obj) {
        ws.send(JSON.stringify(obj));
    };
    return connection;
}


$(function init(){
    var wb = WhitebroadConnection(),
        canvas = document.getElementById('whiteboard'),
        currentHash = "",
        lastKnownServerHash = "?";
    function whiteOut(ctx) {
        ctx.fillStyle = "rgba(255,255,255,255)";
        ctx.fillRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    };
    function drawPixel(evt) {
        wb.send({
            set:
                {
                    x: evt.offsetX,
                    y: evt.offsetY,
                    r: 0,
                    g: 0,
                    b: 0
                }
            });
        return false;
    }
    function doRefresh(context) {
        //Download PNG value and draw it on the canvas
        var img = $('<img />').attr("src", "png/public.png");
        img.on("load", function() {
            context.drawImage(img.get(0), 0, 0);
        })

    }
    function calculateHash(context) {
        var imgd = context.getImageData(0, 0, context.canvas.width, context.canvas.height),
            pix = imgd.data
            pixels = [];
        for (var i = 0, n = pix.length; i < n; i += 4) {
            pixels.push(pix[i]);
            pixels.push(pix[i + 1]);
            pixels.push(pix[i + 2]);
        }
        return adler32(pixels);
    }

    wb.onOpen = function() {
        wb.send({size: "?"});
    };
    wb.onMessage = function(msg) {
        if(msg.hash) {
            lastKnownServerHash = msg.hash;
        }
        if(msg.size) {
            $(canvas).remove();
            $('body').append($('<canvas id="whiteboard" width="' + msg.size.w + '" height="' + msg.size.h + '"/>'))
            canvas = document.getElementById('whiteboard');
            ctx = canvas.getContext("2d");
            c = $(canvas)
            c.on('mousemove', function clickMoveIsDraw(evt) {
                if(evt.which === 1) {
                    return drawPixel(evt);
                }
                return true;
            });
            c.on('click', drawPixel);
            whiteOut(ctx);
        } else if (msg.set) {
            ctx = canvas.getContext("2d");
            ctx.fillStyle = "rgb("
                + msg.set.r + ","
                + msg.set.g + ","
                + msg.set.b + ")";
            ctx.fillRect(msg.set.x, msg.set.y, 1, 1);
            currentHash = String(calculateHash(ctx));
        }
        if(currentHash !== lastKnownServerHash) {
            console.log("Refreshing because " + currentHash + " is not " + lastKnownServerHash);
            ctx = canvas.getContext("2d");
            doRefresh(ctx);
        }
    };
    wb.onClose = function(evt) {
        console.log(evt);
    }
});
