/*
 Copyright (c) 2008 Frank Salim

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.
 */

/*
 * pickle.js
 * a JavaScript module for parsing and serializing Python objects
 */

/* Opcodes
 * !.. not all opcodes are currently supported!
 * ... 1.0 should support all opcodes in pickle v0 (text)
 */
var MARK        = "("
var STOP        = "."

var INT         = "I"
var FLOAT       = "F"
var NONE        = "N"
var STRING      = "S"

var APPEND      = "a"
var DICT        = "d"
var GET         = "g"
var LIST        = "l"
var PUT         = "p"
var SETITEM     = "s"
var TUPLE       = "t"

var TRUE        = "I01\n"
var FALSE       = "I00\n"

/* Other magic constants that are not opcodes
 */
NEWLINE         = "\n"
MARK_OBJECT     = null
SQUO            = "'"

/*
 * loads(string) -> object
 * load a pickled Python object from a string
 */

exports.loads = loads;
function loads(pickle) {
    stack = []
    memo = []

    var ops = pickle.split(NEWLINE)
    var op

    for (var i=0; i<ops.length; i++) {
        op = ops[i]
        process_op(op, memo, stack)
    }
    return stack.pop()
}

// to speed up op processing, declare two args here
var arg0
var arg1

var process_op = function(op, memo, stack) {
    if (op.length === 0)
        return

    switch (op[0]) {
        case MARK:
            // TODO: when we support POP_MARK AND POP, we need real marks
            // ...we need this for tuple, as well
            //stack.push(MARK_OBJECT)
            process_op(op.slice(1), memo, stack)
            break
        case STOP:
            //console.log("stop")
            break
        case INT:
            // booleans are a special case of integers
            if (op[1] === "0") {
                arg0 = (op[2] === "1")
                stack.push(arg0)
                break
            }
       
            arg0 = parseInt(op.slice(1))
            //console.log("int", arg0)
            stack.push(arg0)
            break
        case FLOAT:
            arg0 = parseFloat(op.slice(1))
            //console.log("int", arg0)
            stack.push(arg0)
            break
        case STRING:
            arg0 = eval(op.slice(1))
            stack.push(arg0)
            //console.log("string", arg0)
            break
        case NONE:
            stack.push(null)
            process_op(op.slice(1), memo, stack)
            break
        case APPEND:
            arg0 = stack.pop()
            //console.log("appending to", stack[stack.length-1])
            stack[stack.length-1].push(arg0)
            process_op(op.slice(1), memo, stack)
            break
        case DICT:
            stack.push({})
            process_op(op.slice(1), memo, stack)
            break
        case GET:
            arg0 = parseInt(op.slice(-1))
            arg1 = memo[arg0]
            stack.push(arg1)
            //console.log("getting", arg1)
            break
        case LIST:            
            stack.push([])
            process_op(op.slice(1), memo, stack)
            break
        case PUT:
            arg0 = parseInt(op.slice(-1))
            arg1 = stack[stack.length-1]
            memo[arg0] = arg1
            //console.log("memo", arg0, arg1)
            break
        case SETITEM:
            arg1 = stack.pop()
            arg0 = stack.pop()
            stack[stack.length-1][arg0] = [arg1]
            //console.log("current before set", stack)
            process_op(op.slice(1), memo, stack)
            break
        case TUPLE:
            //console.log("tuple")
            stack.push([])
            // TODO: tuples
           
            process_op(op.slice(1))
            break    
        default:
            throw new Error("unknown opcode " + op[0])
    }      

}

/*
 * dumps(object) -> string
 * serializes a JavaScript object to a Python pickle
 */
exports.dumps = dumps;
function dumps(obj) {
    // pickles always end with a stop
    return _dumps(obj) + STOP
}

var _check_memo = function(obj, memo) {
    for (var i=0; i<memo.length; i++) {
        if (memo[i] === obj) {
            return i
        }
    }
    return -1
}

var _dumps = function(obj, memo) {
    memo = memo || []
    if (obj === null) {
        return NONE
    }

    if (typeof(obj) === "object") {
        var p = _check_memo(obj, memo)
        if (p !== -1) {
            return GET + p + NEWLINE
        }
       
        var t = obj.constructor.name
        switch (t) {
            case Array().constructor.name:
                var s = MARK + LIST + PUT + memo.length + NEWLINE
                memo.push(obj)

                for (var i=0; i<obj.length; i++) {
                    s += _dumps(obj[i], memo) + APPEND
                }
                return s
                break
            case Object().constructor.name:
                var s = MARK + DICT + PUT + memo.length + NEWLINE
                memo.push(obj)
               
                for (var key in obj) {
                    //console.log(key)
                    //push the value, then the key, then 'set'
                    s += _dumps(obj[key], memo)
                    s += _dumps(key, memo)
                    s += SETITEM
                }                    
                return s
                break
            default:
                throw new Error("Cannot pickle this object: " + t)
       
        }
    } else if (typeof(obj) === "string") {
        var p = _check_memo(obj, memo)
        if (p !== -1) {
            return GET + p + NEWLINE
        }
       
        var escaped = obj.replace("\\","\\\\","g")
                        .replace("'", "\\'", "g")
                        .replace("\n", "\\n", "g")

        var s = STRING + SQUO + escaped + SQUO + NEWLINE
                + PUT + memo.length + NEWLINE
        memo.push(obj)
        return s
    } else if (typeof(obj) === "number") {
        return FLOAT + obj + NEWLINE
    } else if (typeof(obj) === "boolean") {
        return obj ? TRUE : FALSE
    } else {
        throw new Error("Cannot pickle this type: " + typeof(obj))
    }
}
