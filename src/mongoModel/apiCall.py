# import mongoose from "mongoose";
# const apiCall = new mongoose.Schema({
#   org_id: {
#     type: String,
#     default: ""
#   },
#   bridge_id: {
#     type: String,
#     default: ""
#   },
#   activated: {
#     type: Boolean,
#     default: false
#   },
#   required_fields: {
#     type: [String],
#     default: []
#   },
#   code: {
#     type: String,
#     // required: true,
#     default: ''
#   },
#   fields: { // structure is 
#     type: [Object],
#     /*  [
#           {
#               variable_name:"",
#               description:"",
#               enum:""
#           } 
#         ]*/
#     default: []
#   },
#   endpoint: {  // name of the flow 
#     // COMPLETE IT
#     type: String,
#     default: ""
#   },
#   description: {
#     type: String
#   },
#   created_at: {
#     type: Date,
#     default: Date.now
#   },
#   name: { // function name, scriptId in case of viasocket function
#     type: String,
#     default: ""
#   }
# });
# const apiCallModel = mongoose.model("apicall", apiCall);
# export default apiCallModel;
