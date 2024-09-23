import axios from "axios";
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

// Appコンポーネントを定義し、状態とイベントハンドラを設定
export default function App() {
  const [comment, setComment] = useState("");
  const [comments, setComments] = useState([]);
  const [selectedUser, setSelectedUser] = useState("ryota");
  const [selectedAction, setSelectedAction] = useState("withAI");

  // コンポーネントがマウントされたときにローカルストレージからコメントを読み込む
  useEffect(() => {
    const savedComments = localStorage.getItem("comments");
    if (savedComments) {
      setComments(JSON.parse(savedComments));
    }
  }, []);

  // コメントをローカルストレージに保存する関数
  const saveCommentsToLocalStorage = (comments) => {
    localStorage.setItem("comments", JSON.stringify(comments));
  };

  // コメントをすべて削除する関数
  const handleClearComments = () => {
    localStorage.removeItem("comments");
    setComments([]);
  };

  // Post Commentボタンが押された時に実行される関数
  const handleSubmit = (e) => {
    e.preventDefault();

    // 新しいコメントを追加
    const newComment = {
      text: comment,
      aiResponse: "",
      user: selectedUser,
    };

    if (selectedAction === "withAI") {
      // コメントをAPIに送信
      const data = {
        query: comment, // 入力されたコメントをPOSTする
      };

      axios.post('http://localhost:5050/run-python-string-query', data, {
        headers: {
          'Content-Type': 'application/json',
        },
      })
      .then(response => {
        console.log('Response:', response.data);
        newComment.aiResponse = '地図をご覧ください。Please see the map.';
        const updatedComments = [...comments, newComment];
        setComments(updatedComments);
        saveCommentsToLocalStorage(updatedComments);
      })
      .catch(error => {
        console.error('Error:', error);
        newComment.aiResponse = '地理情報処理に失敗しました。';
        const updatedComments = [...comments, newComment];
        setComments(updatedComments);
        saveCommentsToLocalStorage(updatedComments);
      });
    } else {
      const updatedComments = [...comments, newComment];
      setComments(updatedComments);
      saveCommentsToLocalStorage(updatedComments);
    }

    setComment(""); // テキストエリアをクリア
  };

  return (
    <>
      <div className="h-screen flex flex-wrap flex-row">
        <div className="w-1/3"></div>
        <div className="w-1/3"></div>
        <div className="w-1/3">
          <div className="w-full bg-white rounded-lg border p-2">
            <h3 className="font-bold">Discussion</h3>
            <form onSubmit={handleSubmit}>
              <div className="flex flex-col">
                {comments.map((comment, index) => (
                  <div key={index} className="border rounded-md p-3 ml-3 my-3">
                    <div className="flex gap-3 items-center">
                      <img
                        src={`./images/${comment.user}.png`}
                        className="object-cover w-12 h-12 rounded-full border-2 border-emerald-400 shadow-emerald-400"
                        alt="User avatar"
                      />
                      <h3 className="font-bold">{comment.user}</h3>
                    </div>
                    <p className="text-gray-600 mt-2">{comment.text}</p>
                    {comment.aiResponse && (
                      <div className="flex gap-3 items-center mt-4">
                        <img
                          src="./images/ai.png"
                          className="object-cover w-12 h-12 rounded-full border-2 border-emerald-400 shadow-emerald-400"
                          alt="AI avatar"
                        />
                        <h3 className="font-bold">AI</h3>
                        <p className="text-gray-600 mt-2">{comment.aiResponse}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="w-full px-3 my-2">
                <textarea
                  className="bg-gray-100 rounded border border-gray-400 leading-normal resize-none w-full h-20 py-2 px-3 font-medium placeholder-gray-700 focus:outline-none focus:bg-white"
                  name="body"
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="コメントを入力"
                  required
                ></textarea>
              </div>

              <div className="w-full px-3 my-2">
                <select
                  className="bg-gray-100 rounded border border-gray-400 leading-normal w-full py-2 px-3 font-medium placeholder-gray-700 focus:outline-none focus:bg-white"
                  value={selectedUser}
                  onChange={(e) => setSelectedUser(e.target.value)}
                >
                  <option value="ryota">ryota</option>
                  <option value="hiroshi">hiroshi</option>
                  <option value="chris">chris</option>
                  <option value="ayaka">ayaka</option>
                </select>
              </div>

              <div className="w-full px-3 my-2">
                <select
                  className="bg-gray-100 rounded border border-gray-400 leading-normal w-full py-2 px-3 font-medium placeholder-gray-700 focus:outline-none focus:bg-white"
                  value={selectedAction}
                  onChange={(e) => setSelectedAction(e.target.value)}
                >
                  <option value="withAI">AIに聞く (AI Mode)</option>
                  <option value="withoutAI">コメントのみ (Comment Only)</option>
                </select>
              </div>

              <div className="w-full flex justify-end px-3 gap-2">
                <input
                  type="submit"
                  className="px-2.5 py-1.5 rounded-md text-white text-sm bg-indigo-500"
                  value="コメントを送信"
                />
                <button
                  onClick={handleClearComments}
                  className="px-2.5 py-1.5 rounded-md text-white text-sm bg-indigo-500"
                >
                  コメントを削除
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}

// ReactコンポーネントをDOMにレンダリング
export function renderToDOM(container) {
  createRoot(container).render(<App />);
}