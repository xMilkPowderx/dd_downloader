function filterGlobal (table) {
	var reg = $('#global_regex').prop('checked');
	table.search(
		$('#global_filter').val(),reg,!reg).draw();
}
function filterColumn (table, i) {
	var reg = $('#col'+i+'_regex').prop('checked');
	table.column( i ).search(
		$('#col'+i+'_filter').val(),reg,!reg).draw();
}
function batch_download_command() {
	arr = table.rows({selected: true}).data();
	if (arr.length <= 0) return;
	pks = [];
	for (var i = 0; i < arr.length; i++) {
		pks.push(arr[i]['PK']);
	}
	if (!confirm("You are about to batch-download " + pks.length + " scan(s). Are you sure?")) {
		return;
	}
	var form = $('<form method=post action="{% url "dd_downloader:batch download endpoint" %}">{% csrf_token %}</form>');
	for (var i = 0; i < pks.length; i++) {
		form.append($('<input>',{'name':"pk_list[]", 'value':pks[i]}));
	}
	form.appendTo('body').submit().remove();
}

function scan_batch_command(command) {
	arr = table.rows({selected: true}).data();
	if (arr.length <= 0) return;
	pks = [];
	for (var i = 0; i < arr.length; i++) {
		pks.push(arr[i]['PK']);
	}
	let msg = "unknown"
	switch(command) {
		case 'CR': msg = "create"; break;
		case 'ST': msg = "start"; break;
		case 'PS': msg = "pause"; break;
		case 'RS': msg = "resume"; break;
		case 'SP': msg = "stop"; break;
		case 'RT': msg = "retrieve"; break;
		case 'DL': msg = "delete"; break;
	}
	if (!confirm("You are about to batch-" + msg + " " + pks.length + " scan(s). Are you sure?")) {
		return;
	}
	$.post({
		type: 'POST',
		url: "{% url 'dd_downloader:batch control ajax' %}",
		headers: {'X-CSRFToken': '{{ csrf_token }}'},
		data: {'type': 'scan', 'command': command,'pk_list': pks},
		success: function(data) {
			table.ajax.reload(null, false);
			if (data['status'] == 'success') {alert('Commands successfully issued.');}
			else if (data['status'] == 'failure') {
				let msg = "";
				if ('unsuccessful' in data) {msg += "Command unsuccessful on: " + data['unsuccessful'] + "\n\n";}
				if ('missing' in data) {msg += "Objects not found for PKs: " + data['missing'];}
				alert(msg);
			}
			else if ('status' in data) {alert(data['status']);}
		}
	});
}

function scanner_batch_command(command) {
	arr = table.rows({selected: true}).data();
	if (arr.length <= 0) return;
	pks = [];
	for (var i = 0; i < arr.length; i++) {
		pks.push(arr[i]['PK']);
	}
	let msg = "unknown"
	switch(command) {
		case 'DL':
			msg = "delete"; break;
	}
	if (!confirm("You are about to batch-" + msg + " " + pks.length + " scanner(s). Are you sure?")) {
		return;
	}
	$.post({
		type: 'POST',
		url: "{% url 'dd_downloader:batch control ajax' %}",
		headers: {'X-CSRFToken': '{{ csrf_token }}'},
		data: {'type': 'scanner', 'command': command,'pk_list': pks},
		success: function(data) {
			if (data['status'] == 'success') {alert('Success');}
			else if (data['status'] == 'invalid command') {alert('Invalid command issued');}
			else if (data['status'] == 'failure') {
				let msg = "Command unsuccessful on: " + data['unsuccessful'] + " and scanner objects not found for PKs: " + data['missing'];
				alert(msg);
			}
		}
	});
}

function render_automation(data, type, row, meta) {
	return (data['Auto Create'] ? 'C' : ' ')
		 + (data['Auto Start'] ? 'S' : ' ')
		 + (data['Auto Retrieve'] ? 'R' : ' ');
}
function render_hyperlink(data, type, row, meta) {return '<a href="'+data['URL']+'">'+data['Name']+'</a>';}
function render_datetime(data, type, row, meta) {if (data !== null) {return moment(new Date(data)).format("YYYY-MM-DD HH:mm:ss");} else return '-';}
var create_date_start;
var create_date_end;
var start_date_start;
var start_date_end;
var end_date_start;
var end_date_end;