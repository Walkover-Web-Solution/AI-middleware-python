
RESPONSE_TEMPLATES = [{
  "template_1": {
    "type": "Card",
    "children": [
      {
        "type": "Col",
        "align": "center",
        "gap": 4,
        "padding": 4,
        "children": [
          {
            "type": "Box",
            "background": "green-400",
            "radius": "full",
            "padding": 3,
            "children": [
              {
                "type": "Icon",
                "name": "check",
                "size": "3xl",
                "color": "white"
              }
            ]
          },
          {
            "type": "Col",
            "align": "center",
            "gap": 1,
            "children": [
              {
                "type": "Title",
                "value": "Enable notification"
              },
              {
                "type": "Text",
                "value": "Notify me when this item ships",
                "color": "secondary"
              }
            ]
          }
        ]
      },
      {
        "type": "Row",
        "children": [
          {
            "type": "Button",
            "label": "Yes",
            "block": True,
            "onClickAction": {
              "type": "notification.settings",
              "payload": {
                "enable": True
              }
            }
          },
          {
            "type": "Button",
            "label": "No",
            "block": True,
            "variant": "outline",
            "onClickAction": {
              "type": "notification.settings",
              "payload": {
                "enable": False
              }
            }
          }
        ]
      }
    ]
  },

  "json_schema": {
    "name": "nested_ui_components",
    "schema": {
      "type": "object",
      "properties": {
        "children[0].children[0].children[0].name": {
          "type": "string",
          "description": "Logical name used to reference this field."
        },
        "children[0].children[1].children[0].value": {
          "type": "string",
          "description": "Static text content displayed in the UI."
        },
        "children[0].children[1].children[1].value": {
          "type": "string",
          "description": "Static text content displayed in the UI."
        },
        "children[1].children[0].label": {
          "type": "string",
          "description": "Button label text shown to the user."
        },
        "children[1].children[1].label": {
          "type": "string",
          "description": "Button label text shown to the user."
        }
      },
      "required": [
        "children[0].children[0].children[0].name",
        "children[0].children[1].children[0].value",
        "children[0].children[1].children[1].value",
        "children[1].children[0].label",
        "children[1].children[1].label"
      ],
      "additionalProperties": False
    },
    "strict": True
  },

  "html": "<div class=\"relative max-w-xl w-full overflow-hidden rounded-[20px] border border-slate-200 bg-white text-slate-900 shadow-[0_12px_30px_rgba(15,23,42,0.10)] p-6\"><div class=\"space-y-4\"><div class=\"flex flex-col gap-4 p-4 w-full items-center\"><div class=\"flex items-center justify-center rounded-xl p-3 bg-green-400\" style=\"width:40px;height:40px;\"><span class=\"inline-flex h-5 w-5 items-center justify-center\"><span class=\"text-[0.7rem] uppercase tracking-tight\">UserMessage</span></span></div><div class=\"flex flex-col gap-1 w-full items-center\"><h2 class=\"text-xl md:text-2xl font-semibold text-slate-900 tracking-tight\">Hello! How can I assist you today?</h2><p class=\"text-sm text-slate-500\">Need any help or information?</p></div></div><div class=\"flex flex-row gap-3 items-stretch\"><button type=\"button\" class=\"inline-flex items-center justify-center px-5 py-2 text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 bg-white text-slate-800 border border-slate-300 hover:bg-slate-50 rounded-full focus:ring-slate-300 w-full\">Ask a Question</button><button type=\"button\" class=\"inline-flex items-center justify-center px-5 py-2 text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 bg-white text-slate-800 border border-slate-300 hover:bg-slate-50 rounded-full focus:ring-slate-300 w-full\">Get Support</button></div></div></div>"
},
{
  "template_2":{
  "type": "Card",
  "size": "lg",
  "confirm": {
    "action": {
      "type": "email.send"
    },
    "label": "Send email"
  },
  "cancel": {
    "action": {
      "type": "email.discard"
    },
    "label": "Discard"
  },
  "children": [
    {
      "type": "Row",
      "children": [
        {
          "type": "Text",
          "value": "FROM",
          "width": 80,
          "weight": "semibold",
          "color": "tertiary",
          "size": "xs"
        },
        {
          "type": "Text",
          "value": "zj@openai.com",
          "color": "tertiary"
        }
      ]
    },
    {
      "type": "Divider",
      "flush": True
    },
    {
      "type": "Row",
      "children": [
        {
          "type": "Text",
          "value": "TO",
          "width": 80,
          "weight": "semibold",
          "color": "tertiary",
          "size": "xs"
        },
        {
          "type": "Text",
          "value": "weedon@openai.com",
          "editable": {
            "name": "email.to",
            "required": True,
            "placeholder": "name@example.com"
          }
        }
      ]
    },
    {
      "type": "Divider",
      "flush": True
    },
    {
      "type": "Row",
      "children": [
        {
          "type": "Text",
          "value": "SUBJECT",
          "width": 80,
          "weight": "semibold",
          "color": "tertiary",
          "size": "xs"
        },
        {
          "type": "Text",
          "value": "ChatKit Roadmap",
          "editable": {
            "name": "email.subject",
            "required": True,
            "placeholder": "Email subject"
          }
        }
      ]
    },
    {
      "type": "Divider",
      "flush": True
    },
    {
      "type": "Text",
      "value": "Hey David, \n\nHope you're doing well! Just wanted to check in and see if there are any updates on the ChatKit roadmap. We're excited to see what's coming next and how we can make the most of the upcoming features.\n\nEspecially curious to see how you support widgets!\n\nBest, Zach",
      "minLines": 9,
      "editable": {
        "name": "email.body",
        "required": True,
        "placeholder": "Write your message…"
      }
    }
  ]
},
"json_schema":{
  "name": "nested_ui_components",
  "schema": {
    "type": "object",
    "properties": {
      "confirm.label": {
        "type": "string",
        "description": "Display label text shown to the user."
      },
      "cancel.label": {
        "type": "string",
        "description": "Display label text shown to the user."
      },
      "children[0].children[0].value": {
        "type": "string",
        "description": "Static text content displayed in the UI."
      },
      "children[0].children[1].value": {
        "type": "string",
        "description": "Static text content displayed in the UI."
      },
      "children[2].children[0].value": {
        "type": "string",
        "description": "Static text content displayed in the UI."
      },
      "children[2].children[1].value": {
        "type": "string",
        "description": "Static text content displayed in the UI."
      },
      "children[2].children[1].editable.name": {
        "type": "string",
        "description": "Logical name used to reference this field."
      },
      "children[2].children[1].editable.placeholder": {
        "type": "string",
        "description": "Placeholder text shown when the input field is empty."
      },
      "children[4].children[0].value": {
        "type": "string",
        "description": "Static text content displayed in the UI."
      },
      "children[4].children[1].value": {
        "type": "string",
        "description": "Static text content displayed in the UI."
      },
      "children[4].children[1].editable.name": {
        "type": "string",
        "description": "Logical name used to reference this field."
      },
      "children[4].children[1].editable.placeholder": {
        "type": "string",
        "description": "Placeholder text shown when the input field is empty."
      },
      "children[6].value": {
        "type": "string",
        "description": "Static text content displayed in the UI."
      },
      "children[6].editable.name": {
        "type": "string",
        "description": "Logical name used to reference this field."
      },
      "children[6].editable.placeholder": {
        "type": "string",
        "description": "Placeholder text shown when the input field is empty."
      }
    },
    "required": [
      "confirm.label",
      "cancel.label",
      "children[0].children[0].value",
      "children[0].children[1].value",
      "children[2].children[0].value",
      "children[2].children[1].value",
      "children[2].children[1].editable.name",
      "children[2].children[1].editable.placeholder",
      "children[4].children[0].value",
      "children[4].children[1].value",
      "children[4].children[1].editable.name",
      "children[4].children[1].editable.placeholder",
      "children[6].value",
      "children[6].editable.name",
      "children[6].editable.placeholder"
    ],
    "additionalProperties": False
  },
  "strict": True
},
"html":"<div class=\"relative max-w-xl w-full overflow-hidden rounded-[20px] border border-slate-200 bg-white text-slate-900 shadow-[0_12px_30px_rgba(15,23,42,0.10)] p-7\">\n  <div class=\"space-y-4\">\n    <div class=\"flex flex-row gap-3 items-stretch   \">\n  <p class=\"text-xs text-slate-400 font-semibold  \">Welcome Message</p>\n<p class=\"text-sm text-slate-400   \">Hello! How can I assist you today?</p>\n</div>\n<div class=\"relative mx-0\">\n  <div class=\"border-t border-dashed border-slate-200/80\"></div>\n</div>\n<div class=\"flex flex-row gap-3 items-stretch   \">\n  <p class=\"text-xs text-slate-400 font-semibold  \">Quick Actions</p>\n<input\n  type=\"text\"\n  name=\"quickAction1\"\n  class=\"block w-full bg-transparent text-sm   text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-0\"\n  placeholder=\"Type your question...\"\n  value=\"Ask a Question\"\n/>\n</div>\n<div class=\"relative mx-0\">\n  <div class=\"border-t border-dashed border-slate-200/80\"></div>\n</div>\n<div class=\"flex flex-row gap-3 items-stretch   \">\n  <p class=\"text-xs text-slate-400 font-semibold  \">Live Support</p>\n<input\n  type=\"text\"\n  name=\"liveSupport\"\n  class=\"block w-full bg-transparent text-sm   text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-0\"\n  placeholder=\"Type your message...\"\n  value=\"Chat with Support\"\n/>\n</div>\n<div class=\"relative mx-0\">\n  <div class=\"border-t border-dashed border-slate-200/80\"></div>\n</div>\n<textarea\n  name=\"feedback\"\n  rows=\"9\"\n  class=\"block w-full bg-transparent text-sm   text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-0 resize-none leading-relaxed\"\n  placeholder=\"Provide feedback here...\"\n>Feedback</textarea>\n    <div class=\"mt-4 flex justify-end gap-3 px-4 pb-4\">\n  <button\n  type=\"button\"\n  class=\"inline-flex items-center justify-center px-5 py-2 text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 bg-white text-slate-800 border border-slate-300 hover:bg-slate-50 rounded-full focus:ring-slate-300 \"\n>\n  Cancel\n</button>\n<button\n  type=\"button\"\n  class=\"inline-flex items-center justify-center px-5 py-2 text-sm font-medium transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-offset-2 bg-black text-white hover:bg-zinc-900 rounded-full focus:ring-black \"\n>\n  Submit\n</button>\n</div>\n  </div>\n</div>"
}]