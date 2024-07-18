responsePrompt = """{
  "purpose": "Modify given response so that we can display it beautifully using Material UI components and make it actionable by adding actions to buttons",
  "instructions": "1. Minimize words by using variable paths (variables.key) in components and actions."
  "2. Add actions only to the Button component and compulsory show the UI component to display information to the user."
 "3. give valid response in available max tokens"
  "available_components": ["Table", "Button", "Typography", "TextField"],
  "output_json_format": {
    "isMarkdown": false,
    "variables": {
      "<key>": "<value>"
    },
    "components": {
      "<component_name>": {
        "type": "<component_type>",
        "props": {
          "<key>": "variables.<key>"
        }
      },
      "Button": {
        "type": "Button",
        "props": {
          "<key>": "variables.<key>"
        },
        "action": {
          actionId : <actionId>
          actionType : <action_Type>
          "variables": {
            // fill all the json values with the variables path
            "<key_from_available_actions_varible>": <path from variables>
          }
        }
      }
    }
  }
}"""
