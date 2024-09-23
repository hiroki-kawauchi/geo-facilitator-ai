from langchain_core.messages import HumanMessage
import json
import os


def function_calling(llm, tools, tool_names, query):
    '''
    LLMとツールを結合し、クエリに対して処理を実行する関数。

    Args:
    - llm: 言語モデルのインスタンス。
    - tools: 使用するツールのリスト。
    - tool_names: 使用するツールの名前の辞書。
    - query: ユーザーからの入力クエリ。
    - output_path: 出力先ディレクトリパス。

    Returns:
    - JSON形式でツールの出力を含む辞書。
    '''

    # LLMモデルとツールを結合して、新しいLLMインスタンスを作成
    llm_with_tools = llm.bind_tools(tools)

    # クエリをHumanMessageオブジェクトに変換
    messages = [HumanMessage(query)]

    # LLMを使用してメッセージに対する応答を取得
    ai_msg = llm_with_tools.invoke(messages)

    # AIからの応答メッセージをメッセージリストに追加
    messages.append(ai_msg)

    # ツールの出力を格納する辞書を初期化
    list_tool_outputs = list()

    # AIメッセージからツール呼び出しを取得し、対応するツールを実行
    for tool_call in ai_msg.tool_calls:
        # ツール名に基づいてツールを選択
        selected_tool = tool_names[tool_call['name']]
        # print(f"selected tool: {tool_call}")

        # ツールを実行し、出力を取得
        tool_output = selected_tool.invoke(tool_call['args'])

        # 出力を辞書に追加
        list_tool_outputs.append(tool_output)

    # ツールの出力辞書をJSON形式で返す
    return list_tool_outputs