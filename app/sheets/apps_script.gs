/**
 * Configure API_BASE_URL and API_TOKEN in Apps Script Properties.
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Pokémon Price')
    .addItem('Processar linha atual', 'processCurrentRow')
    .addItem('Processar lote (linhas selecionadas)', 'processSelectedRows')
    .addToUi();
}

function COMPARAR_CARTA(nome, condicao, edicao) {
  if (!nome || !condicao || !edicao) {
    return [['', '', '', '', 'INDEFINIDO', 'DADOS INSUFICIENTES', 'ENTRADA INVÁLIDA', '', '']];
  }
  var result = callCompareApi_({ nome: nome, condicao: condicao, edicao: edicao });
  return [[
    result.preco_liga || '',
    result.preco_myp || '',
    result.diferenca_reais || '',
    result.diferenca_percentual || '',
    result.melhor_opcao || 'INDEFINIDO',
    result.vale_a_pena_comprar_no_myp || 'DADOS INSUFICIENTES',
    result.status_log || 'SEM STATUS',
    result.url_liga || '',
    result.url_myp || ''
  ]];
}

function processCurrentRow() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var row = sheet.getActiveCell().getRow();
  processRows_(sheet, [row]);
}

function processSelectedRows() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var range = sheet.getActiveRange();
  var rows = [];
  for (var r = range.getRow(); r < range.getRow() + range.getNumRows(); r++) {
    rows.push(r);
  }
  processRows_(sheet, rows);
}

function processRows_(sheet, rows) {
  var payload = { items: [] };
  var validRows = [];

  rows.forEach(function(row) {
    var nome = sheet.getRange(row, 1).getValue();
    var condicao = sheet.getRange(row, 2).getValue();
    var edicao = sheet.getRange(row, 3).getValue();
    if (nome && condicao && edicao) {
      payload.items.push({ nome: nome, condicao: condicao, edicao: edicao });
      validRows.push(row);
    }
  });

  if (!payload.items.length) return;

  var response = callBatchApi_(payload);
  response.results.forEach(function(result, idx) {
    var row = validRows[idx];
    sheet.getRange(row, 4, 1, 9).setValues([[
      result.preco_liga || '',
      result.preco_myp || '',
      result.diferenca_reais || '',
      result.diferenca_percentual || '',
      result.melhor_opcao || 'INDEFINIDO',
      result.vale_a_pena_comprar_no_myp || 'DADOS INSUFICIENTES',
      result.status_log || 'SEM STATUS',
      result.url_liga || '',
      result.url_myp || ''
    ]]);
  });
}

function callCompareApi_(payload) {
  var baseUrl = PropertiesService.getScriptProperties().getProperty('API_BASE_URL');
  var token = PropertiesService.getScriptProperties().getProperty('API_TOKEN');
  var options = {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    payload: JSON.stringify(payload),
    headers: token ? { 'Authorization': 'Bearer ' + token } : {}
  };
  var resp = UrlFetchApp.fetch(baseUrl + '/compare', options);
  return JSON.parse(resp.getContentText());
}

function callBatchApi_(payload) {
  var baseUrl = PropertiesService.getScriptProperties().getProperty('API_BASE_URL');
  var token = PropertiesService.getScriptProperties().getProperty('API_TOKEN');
  var options = {
    method: 'post',
    contentType: 'application/json',
    muteHttpExceptions: true,
    payload: JSON.stringify(payload),
    headers: token ? { 'Authorization': 'Bearer ' + token } : {}
  };
  var resp = UrlFetchApp.fetch(baseUrl + '/compare/batch', options);
  return JSON.parse(resp.getContentText());
}
