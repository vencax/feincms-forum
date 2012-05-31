tinyMCE.init({
        theme : "advanced",
        plugins : "bbcode",
        theme_advanced_buttons1 : "bold,italic,underline,undo,redo,link,unlink,image,forecolor,blockquote,removeformat,cleanup",
        theme_advanced_buttons2 : "",
        theme_advanced_buttons3 : "",
        theme_advanced_toolbar_align : "center",
        theme_advanced_toolbar_location : "top",
        content_css : "example_data/bbcode.css",
        entity_encoding : "raw",
        add_unload_trigger : false,
        remove_linebreaks : false,
        inline_styles : false,
        convert_fonts_to_spans : false
});

var txt = ''

function copyQ(nick) {
	txt = ''
	if (document.getSelection) {
		txt = document.getSelection()
	} else
	if (document.selection) {
		txt = document.selection.createRange().text;
	}
	txt = '[quote]' + nick + ':\n' + txt + '[/quote]\n'
}

function insertAtCaret (textObj, textFieldValue) {
	if (document.all) {
		if (textObj.createTextRange && textObj.caretPos && !window.opera) {
			var caretPos = textObj.caretPos;
			caretPos.text = caretPos.text.charAt(caretPos.text.length - 1) == ' ' ?textFieldValue + ' ' : textFieldValue;
		} else {
			textObj.value += textFieldValue;
		}
	} else {
		if (textObj.selectionStart) {
			var rangeStart = textObj.selectionStart;
			var rangeEnd = textObj.selectionEnd;
			var tempStr1 = textObj.value.substring(0, rangeStart);
			var tempStr2 = textObj.value.substring(rangeEnd, textObj.value.length);
			textObj.value = tempStr1 + textFieldValue + tempStr2;
			textObj.selectionStart = textObj.selectionEnd = rangeStart + textFieldValue.length;
		} else {
			textObj.value += textFieldValue;
		}
	}
}

function pasteQ() {
	if (txt!='' && document.forms['post']['body'])
	insertAtCaret(document.forms['post']['body'], txt);
}

function pasteN(text) {
	if (text != '' && document.forms['post']['body'])
	insertAtCaret(document.forms['post']['body'], "[b]" + text + "[/b]\n");
}

function asyncAction(url, data, callback) {
	$.ajax({
		type: "POST",
		url: url,
		dataType: "json",
		data : data,
		success: callback,
		error: function(XMLHttpRequest, textStatus, errorThrown) {
			cnt = "reqest" + XMLHttpRequest + "\nstatus:" + textStatus + "\nerror:" + errorThrown;
			alert(cnt);
		}
	});
}

function switchAction(url, node) {
	asyncAction(url, '', function(res) {
		node.innerHTML = res.msg;
	});
}

function deleteAction(url, nodeToRemove, question) {
	if(confirm(question) == true) {
		asyncAction(url, '', function(res) {
			if(res.redir == undefined) {
				removePost(nodeToRemove);
			} else {
				window.location = res.redir;
			}
		});
	}
}

function removePost(node) {
	$('#'+node).remove();
}

function prepareMove(prepareUrl, moveUrl, node) {
	asyncAction(prepareUrl, '', function(res) {
		if($('#moveForm').length == 0) {
			if(res.stat == 'OK') {
				form = _createMoveForm(res.data, moveUrl);
				$(node).after(form);
			} else {
				alert(res.msg);
			}
		}
	});
}

function moveTopic(moveUrl, targetForumId, form) {
	asyncAction(moveUrl, 'forum_id=' + targetForumId, function(res) {
		if(res.stat == 'OK') {
			alert(res.msg);
			form.remove();
			window.location = res.redir;
		} else {
			alert(res.msg);
		}
	});
}

function _createMovebutton(moveUrl, form, ul, forumId, forumName) {
	var butt = $('<a href="javascript: void(0)">' + forumName + '</a>').click(function() {
		moveTopic(moveUrl, forumId, form);
	});
	var li = $('<li></li>');
	$(ul).append(li);
	$(li).append(butt);
}

function _createMoveForm(data, moveUrl) {
	var form = $('<div id="moveForm"></div>');
	var ul = $('<ul style="list-style-type: square; padding-left: 20px;"></ul>');
	$(form).append(ul);
	for(var i = 0; i < data.length; i++) {
		var parts = data[i].split('#');
		_createMovebutton(moveUrl, form, ul, parts[0], parts[1]);
	}
	return form;
}
