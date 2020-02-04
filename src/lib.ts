import { Sheet, SheetSchema } from './sheet'
import { Spreadsheet, SpreadsheetSchema } from './spreadsheet'

// pre-built styles
export const headerStyle = SpreadsheetApp.newTextStyle().setBold(true).build()
export const protectedBackgroundColor = '#ffe5be'

/**
 * Creates and returns a new Spreadsheet object, including all sheets, according
 * to a provided schema object.
 * 
 * @param schema 
 */
export const setupSpreadsheet = (spreadsheet: SpreadsheetSchema): Spreadsheet => {
    const newSpreadsheet = SpreadsheetApp.create(spreadsheet.title) // create a new spreadsheet
    spreadsheet.sheets.forEach(sheet => setupSheet(newSpreadsheet, sheet)) // create all sheets
    newSpreadsheet.deleteSheet(newSpreadsheet.getSheetByName('Sheet1')) // remove the default sheet
    return newSpreadsheet // return created spreadsheet
}

/**
 * Creates a new Sheet on a given Spreadsheet, according to provided schema.
 * Initializes a row of column headers and creates named ranges for each column
 * in the sheet in the format 'sheet_name__field_name'. Returns the finished
 * sheet object.
 * 
 * @param spreadsheet 
 * @param schema 
 */
export const setupSheet = (spreadsheet: Spreadsheet, sheet: SheetSchema): Sheet => {
    const newSheet = spreadsheet.insertSheet(sheet.name) // create the new sheet
    const fieldNames = sheet.fields.map(f => f.name) // get the names of its fields
    
    newSheet // setup the headers
        .appendRow(fieldNames)
        .getDataRange()
        .setTextStyle(headerStyle)
        .setHorizontalAlignment('center')

    newSheet.setFrozenRows(1) // freeze the headers

    // setup the individual fields (columns)
    sheet.fields.map((field, index) => {
        const alpha = indexToAlpha(index) // convert column number to 'A', 'B', 'AB', etc
        const a1notation = `\'${sheet.name}\'!${alpha}2:${alpha}` // e.g. 'Sheet Name'!B2:B, will select all of column B except headers
        const range = spreadsheet.getRange(a1notation) // select all data cells

        // automatically create a named range 'sheet_name__field_name', see:
        // https://developers.google.com/apps-script/reference/spreadsheet/named-range
        const rangeName = `${slugify(sheet.name)}__${slugify(field.name)}`
        spreadsheet.setNamedRange(rangeName, range)

        // add protection if the range should be read-only; see:
        // https://developers.google.com/apps-script/reference/spreadsheet/protection
        if (field.protected) {
            const protection = range.protect()
            const me = Session.getActiveUser()
            const editorEmails = protection.getEditors().map(u => u.getEmail())
            protection.addEditor(me) // ensure we can still edit
            protection.removeEditors(editorEmails) // remove all others
            range.setBackground(protectedBackgroundColor)
        }
    })

    return newSheet // return fully initialized sheet
}

/**
 * Convert a sheet or field name into a form valid for use in named range. Will
 * change spaces to underscores and remove everything not a letter, number or
 * underscore.
 * 
 * For more on named range naming, see:
 * https://support.google.com/docs/answer/63175
 * 
 * @param name 
 */
export const slugify = (name: string): string => {
    return name.toLowerCase().replace(/\s/g, '_').replace(/\W/g, '')
}

/**
 * Converts a zero-based column index in a sheet into its corresponding alpha
 * notation. Column zero is A, column 1 is B, column 26 is AA, etc. Used when
 * selecting cells in a column via "A1 notation", e.g. "A1:A23".
 * 
 * For more on A1 notation, see:
 * https://developers.google.com/sheets/api/guides/concepts#a1_notation
 * 
 * @param index 
 */
export const indexToAlpha = (index: number): string => {
    const digits = index
        .toString(26) // convert to base-26 integer
        .split('') // split into individual digits
        .map(digit => parseInt(digit, 26)) // convert each digit back to base-10 to use as alpha offset

    if (digits.length > 1) digits[0] -= 1 // 0 -> 'A' so for multidigit numbers, adjust the most significant digit

    return digits
        .map(digit => String.fromCharCode(65 + digit)) // use the digit as an offset from 'A' (ASCII 65)
        .join('') // join resulting letters back together
}

// array.find polyfill, see:
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/find#Polyfill
// https://tc39.github.io/ecma262/#sec-array.prototype.find
if (!Array.prototype.find) {
    Object.defineProperty(Array.prototype, 'find', {
      value: function(predicate: any) {
        // 1. Let O be ? ToObject(this value).
        if (this == null) {
          throw TypeError('"this" is null or not defined');
        }
  
        var o = Object(this);
  
        // 2. Let len be ? ToLength(? Get(O, "length")).
        var len = o.length >>> 0;
  
        // 3. If IsCallable(predicate) is false, throw a TypeError exception.
        if (typeof predicate !== 'function') {
          throw TypeError('predicate must be a function');
        }
  
        // 4. If thisArg was supplied, let T be thisArg; else let T be undefined.
        var thisArg = arguments[1];
  
        // 5. Let k be 0.
        var k = 0;
  
        // 6. Repeat, while k < len
        while (k < len) {
          // a. Let Pk be ! ToString(k).
          // b. Let kValue be ? Get(O, Pk).
          // c. Let testResult be ToBoolean(? Call(predicate, T, « kValue, k, O »)).
          // d. If testResult is true, return kValue.
          var kValue = o[k];
          if (predicate.call(thisArg, kValue, k, o)) {
            return kValue;
          }
          // e. Increase k by 1.
          k++;
        }
  
        // 7. Return undefined.
        return undefined;
      },
      configurable: true,
      writable: true
    });
  }