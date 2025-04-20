import React, { useState, useEffect, useRef } from "react";
import {
  MoreVertical,
  Pencil,
  Trash2,
  PlusCircleIcon,
  MessageSquareIcon,
  UserIcon,
  BotIcon,
  SendIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  MicIcon,
  ScrollText,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Dialog } from "@headlessui/react"; // Import Headless UI for modal
import ReactMarkdown from "react-markdown";

interface Chat {
  id: string;
  title: string;
  date: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  context?: Array<{
    ten?: string;
    vbqppl?: string;
    // noidung?: string;
    vbqppl_link?: string;
  }>;
}

const ChatPage = () => {
  const { user } = useAuth(); // Lấy thông tin user từ context
  const [chatHistory, setChatHistory] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | undefined>(
    undefined
  );
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "Xin chào! Tôi là trợ lý pháp luật ảo. Tôi có thể giúp gì cho bạn?",
      timestamp: "",
    },
  ]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newChatTitle, setNewChatTitle] = useState("");

  const generateGuestId = () =>
    `anon_${Date.now()}_${Math.floor(Math.random() * 9000) + 1000}`;
  const [guestId, setGuestId] = useState(generateGuestId());

  const [openMenuId, setOpenMenuId] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editChatId, setEditChatId] = useState<string | null>(null);
  const [editChatTitle, setEditChatTitle] = useState("");
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deleteChatId, setDeleteChatId] = useState<string | null>(null);
  const [deleteChatTitle, setDeleteChatTitle] = useState<string | null>(null);
  const [deleteChatDate, setDeleteChatDate] = useState<string | null>(null);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [showAllContexts, setShowAllContexts] = useState(false);
  const [showContexts, setShowContexts] = useState(false);

  const toggleOptions = (chatId: string) => {
    setOpenMenuId((prev) => (prev === chatId ? null : chatId));
  };

  const openEditModal = (chatId: string, currentTitle: string) => {
    setEditChatId(chatId);
    setEditChatTitle(currentTitle);
    setIsEditModalOpen(true);
  };

  const closeEditModal = () => {
    setIsEditModalOpen(false);
    setEditChatId(null);
    setEditChatTitle("");
  };

  const handleEditChat = async () => {
    if (!editChatId || !editChatTitle.trim()) return;

    try {
      const response = await fetch(
        `http://localhost:5000/api/v1/auth/conversation/${editChatId}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({ title: editChatTitle }),
        }
      );

      if (response.ok) {
        setChatHistory((prev) =>
          prev.map((chat) =>
            chat.id === editChatId ? { ...chat, title: editChatTitle } : chat
          )
        );
        console.log("Cập nhật tiêu đề thành công");
      } else {
        console.error("Lỗi khi cập nhật tiêu đề:", await response.json());
      }
    } catch (error) {
      console.error("Lỗi khi gọi API cập nhật tiêu đề:", error);
    }

    closeEditModal();
  };

  const openDeleteModal = (
    chatId: string,
    chatTitle: string,
    chatDate: string
  ) => {
    setDeleteChatId(chatId);
    setDeleteChatTitle(chatTitle);
    setDeleteChatDate(chatDate);
    setIsDeleteModalOpen(true);
  };

  const closeDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setDeleteChatId(null);
    setDeleteChatTitle(null);
    setDeleteChatDate(null);
  };

  const handleDeleteChat = async () => {
    if (!deleteChatId) return;

    try {
      const response = await fetch(
        `http://localhost:5000/api/v1/auth/conversation/${deleteChatId}`,
        {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        setChatHistory((prev) =>
          prev.filter((chat) => chat.id !== deleteChatId)
        );

        // If the deleted chat is the currently selected one, reset the chat window
        if (currentChatId === deleteChatId) {
          setCurrentChatId(undefined);
          setMessages([
            {
              id: "0",
              role: "assistant",
              content:
                "Cuộc hội thoại đã bị xóa. Hãy chọn hoặc tạo một cuộc hội thoại mới.",
              timestamp: new Date().toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              }),
            },
          ]);
        }

        console.log("Xóa cuộc hội thoại thành công");
      } else {
        console.error("Lỗi khi xóa cuộc hội thoại:", await response.json());
      }
    } catch (error) {
      console.error("Lỗi khi gọi API xóa cuộc hội thoại:", error);
    }

    closeDeleteModal();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    const newUserMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    let chatId = currentChatId;

    if (user && !chatId) {
      // Authenticated user without a conversation: create a new one
      try {
        chatId = await handleCreateChat(message); // Use the user's message as the title
        if (!chatId) {
          console.error("Không thể tạo cuộc hội thoại mới");
          return;
        }
        setCurrentChatId(chatId);
      } catch (error) {
        console.error("Lỗi khi tạo cuộc hội thoại:", error);
        return;
      }
    }

    // Append the user's message to the chat window immediately
    setMessages((prev) => [...prev, newUserMessage]);

    try {
      const endpoint = user
        ? `http://localhost:5000/api/v1/auth/question`
        : `http://localhost:5000/api/v1/public/question`;

      const requestBody = user
        ? { question: message, conversation_id: chatId }
        : { question: message, guest_id: guestId };

      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(user
            ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
            : {}),
        },
        body: JSON.stringify(requestBody),
      });

      const data = await response.json();
      if (!data.response) {
        console.error("API không trả về phản hồi hợp lệ:", data);
        return;
      }

      console.log(data.context);

      const botResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || "Xin lỗi, tôi không thể trả lời câu hỏi này.",
        context: data.context || [], // Update context with new data
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      console.error("Lỗi kết nối với backend:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 2).toString(),
          role: "assistant",
          content:
            "Đã xảy ra lỗi khi kết nối với máy chủ. Vui lòng thử lại sau.",
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    }
  };

  const fetchConversationMessages = async (conversationId: string) => {
    try {
      const response = await fetch(
        `http://localhost:5000/api/v1/auth/conversation/${conversationId}/messages`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setMessages(
          data.messages.map((msg: any) => ({
            id: msg._id, // Use _id from the database
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
            context: msg.context || [], // Ensure context is included
          }))
        );
      } else {
        console.error("Failed to fetch messages:", await response.json());
      }
    } catch (error) {
      console.error("Error fetching conversation messages:", error);
    }
  };

  const handleSelectConversation = (conversationId: string) => {
    setCurrentChatId(conversationId);
    fetchConversationMessages(conversationId);
  };

  const openModal = () => setIsModalOpen(true);
  const closeModal = () => {
    setIsModalOpen(false);
    setNewChatTitle("");
  };

  const handleCreateChat = async (
    newChatTitle: string
  ): Promise<string | undefined> => {
    if (!newChatTitle.trim()) return undefined;

    let newChatId = Date.now().toString(); // Temporary ID

    if (user) {
      try {
        const response = await fetch(
          "http://localhost:5000/api/v1/auth/conversation",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${localStorage.getItem("token")}`,
            },
            body: JSON.stringify({ title: newChatTitle }),
          }
        );

        if (response.ok) {
          const data = await response.json();
          newChatId = data.conversation_id; // Update ID from API
        } else {
          console.error("Lỗi tạo cuộc hội thoại:", await response.json());
          return undefined;
        }
      } catch (error) {
        console.error("Lỗi khi gọi API tạo cuộc hội thoại:", error);
        return undefined;
      }
    }

    const newChat = {
      id: newChatId,
      title: newChatTitle,
      date: new Date().toLocaleDateString("vi-VN"),
    };

    setChatHistory((prev) => [newChat, ...prev]);
    setCurrentChatId(newChatId); // Automatically select the new chat
    setMessages([
      {
        id: "0",
        role: "assistant",
        content:
          "Xin chào! Tôi là trợ lý pháp luật ảo. Tôi có thể giúp gì cho bạn?",
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);

    if (isModalOpen) {
      closeModal();
    }

    return newChatId;
  };

  const fetchUserConversations = async () => {
    try {
      const response = await fetch(
        "http://localhost:5000/api/v1/auth/conversations",
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setChatHistory(
          data.conversations.map((conv: any) => ({
            id: conv.id,
            title: conv.title,
            date: conv.date,
          }))
        );
      } else {
        console.error("Failed to fetch conversations:", await response.json());
      }
    } catch (error) {
      console.error("Error fetching user conversations:", error);
    }
  };

  useEffect(() => {
    if (user) {
      fetchUserConversations();
    }
  }, [user]);

  const openLoginModal = () => setIsLoginModalOpen(true);
  const closeLoginModal = () => setIsLoginModalOpen(false);

  const handleNewChatClick = () => {
    if (user) {
      openModal(); // Open the chat creation modal if logged in
    } else {
      openLoginModal(); // Open the login prompt modal if not logged in
    }
  };

  const handleSpeechToText = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Trình duyệt của bạn không hỗ trợ nhận diện giọng nói.");
      return;
    }

    const recognition = new (window as any).webkitSpeechRecognition();
    recognition.lang = "vi-VN"; // Set language to Vietnamese
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      console.log("Bắt đầu nhận diện giọng nói...");
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      console.log("Kết quả nhận diện:", transcript);
      if (textareaRef.current) {
        textareaRef.current.value += transcript; // Append recognized text to textarea
        textareaRef.current.style.height = "auto"; // Adjust height dynamically
        textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Lỗi nhận diện giọng nói:", event.error);
      alert("Đã xảy ra lỗi khi nhận diện giọng nói. Vui lòng thử lại.");
    };

    recognition.onend = () => {
      console.log("Kết thúc nhận diện giọng nói.");
    };

    recognition.start();
  };

  const toggleMenu = () => {
    setIsMenuOpen((prev) => !prev);
  };

  const toggleContextVisibility = () => {
    setShowContexts((prev) => {
      const newState = !prev;
      if (newState) {
        // Scroll to the bottom when showing contexts
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }
      return newState;
    });
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Modal */}
      <Dialog
        open={isModalOpen}
        onClose={closeModal}
        className="fixed z-10 inset-0 overflow-y-auto"
      >
        <div className="flex items-center justify-center min-h-screen px-4">
          <div className="fixed inset-0 bg-black opacity-30" />
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6 z-20">
            <Dialog.Title className="text-lg font-medium text-gray-900">
              Nhập tiêu đề cuộc hội thoại
            </Dialog.Title>
            <input
              type="text"
              value={newChatTitle}
              onChange={(e) => setNewChatTitle(e.target.value)}
              placeholder="Tiêu đề cuộc hội thoại"
              className="mt-4 w-full border border-gray-300 rounded-lg p-2"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={closeModal}
                className="px-4 py-2 bg-gray-200 rounded-lg"
              >
                Hủy
              </button>
              <button
                onClick={() => handleCreateChat(newChatTitle)}
                className="px-4 py-2 bg-pink-500 text-white rounded-lg"
              >
                Tạo
              </button>
            </div>
          </div>
        </div>
      </Dialog>

      {/* Edit Chat Modal */}
      <Dialog
        open={isEditModalOpen}
        onClose={closeEditModal}
        className="fixed z-10 inset-0 overflow-y-auto"
      >
        <div className="flex items-center justify-center min-h-screen px-4">
          <div className="fixed inset-0 bg-black opacity-30" />
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6 z-20">
            <Dialog.Title className="text-lg font-medium text-gray-900">
              Sửa tiêu đề cuộc hội thoại
            </Dialog.Title>
            <input
              type="text"
              value={editChatTitle}
              onChange={(e) => setEditChatTitle(e.target.value)}
              placeholder="Nhập tiêu đề mới"
              className="mt-4 w-full border border-gray-300 rounded-lg p-2"
            />
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={closeEditModal}
                className="px-4 py-2 bg-gray-200 rounded-lg"
              >
                Hủy
              </button>
              <button
                onClick={handleEditChat}
                className="px-4 py-2 bg-pink-500 text-white rounded-lg"
              >
                Lưu
              </button>
            </div>
          </div>
        </div>
      </Dialog>

      {/* Delete Chat Modal */}
      <Dialog
        open={isDeleteModalOpen}
        onClose={closeDeleteModal}
        className="fixed z-10 inset-0 overflow-y-auto"
      >
        <div className="flex items-center justify-center min-h-screen px-4">
          <div className="fixed inset-0 bg-black opacity-30" />
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6 z-20">
            <Dialog.Title className="text-lg font-medium text-gray-900">
              Xác nhận xóa
            </Dialog.Title>
            <p className="mt-4 text-gray-600">
              Bạn có chắc chắn muốn xóa cuộc hội thoại{" "}
              <strong className="truncate block">{deleteChatTitle}</strong>
              được tạo vào ngày <strong>{deleteChatDate}</strong>? Hành động này
              không thể hoàn tác.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={closeDeleteModal}
                className="px-4 py-2 bg-gray-200 rounded-lg"
              >
                Hủy
              </button>
              <button
                onClick={handleDeleteChat}
                className="px-4 py-2 bg-red-500 text-white rounded-lg"
              >
                Xóa
              </button>
            </div>
          </div>
        </div>
      </Dialog>

      {/* Login Prompt Modal */}
      <Dialog
        open={isLoginModalOpen}
        onClose={closeLoginModal}
        className="fixed z-10 inset-0 overflow-y-auto"
      >
        <div className="flex items-center justify-center min-h-screen px-4">
          <div className="fixed inset-0 bg-black opacity-30" />
          <div className="bg-white rounded-lg shadow-lg max-w-md w-full p-6 z-20">
            <Dialog.Title className="text-lg font-medium text-gray-900">
              Vui lòng đăng nhập
            </Dialog.Title>
            <p className="mt-4 text-gray-600">
              Bạn cần đăng nhập để tạo cuộc hội thoại mới. Nhấn nút bên dưới để
              chuyển đến trang đăng nhập.
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <button
                onClick={closeLoginModal}
                className="px-4 py-2 bg-gray-200 rounded-lg"
              >
                Hủy
              </button>
              <button
                onClick={() => (window.location.href = "/login")}
                className="px-4 py-2 bg-pink-500 text-white rounded-lg"
              >
                Đăng nhập
              </button>
            </div>
          </div>
        </div>
      </Dialog>

      <div className="flex flex-grow overflow-hidden">
        {/* Sidebar */}
        <div
          className={`relative flex flex-col transition-all duration-300 bg-[FFF9F4] border border-green-500 rounded-xl ${
            sidebarOpen ? "w-72" : "w-14"
          }`}
        >
          {/* Toggle Button */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="absolute top-1/2 right-[-16px] transform -translate-y-1/2 bg-white border border-green-500 rounded-full p-1 shadow-md z-10"
          >
            {sidebarOpen ? (
              <ChevronLeftIcon className="w-5 h-5 text-gray-600 " />
            ) : (
              <ChevronRightIcon className="w-5 h-5 text-gray-600" />
            )}
          </button>

          {/* Sidebar Content */}
          {sidebarOpen && (
            <>
              <div className="p-4 border-b border-pink-300 flex items-center justify-between">
                <button
                  onClick={handleNewChatClick}
                  className="border border-pink-300 text-pink-500 py-3 px-4 rounded-xl flex items-center gap-2 shadow-sm hover:shadow-md"
                >
                  <PlusCircleIcon className="h-5 w-5" />
                  <span className="font-medium">Cuộc hội thoại mới</span>
                </button>
              </div>
              <div className="flex-grow overflow-y-auto p-3">
                <h2 className="text-xs font-semibold text-pink-500 uppercase tracking-wider px-2 mb-3">
                  Lịch sử hội thoại
                </h2>
                {chatHistory.length === 0 ? (
                  <div className="text-center py-8 text-pink-300">
                    <MessageSquareIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    {user ? (
                      <p>Chưa có cuộc hội thoại nào</p>
                    ) : (
                      <p>Vui lòng đăng nhập để lưu lịch sử hội thoại</p>
                    )}
                  </div>
                ) : (
                  <ul className="space-y-2">
                    {chatHistory.map((chat) => (
                      <li
                        key={chat.id}
                        className="relative flex items-center justify-between group"
                      >
                        <button
                          onClick={() => handleSelectConversation(chat.id)}
                          className={`flex-1 text-left border border-pink-300 rounded-xl p-3 max-w-full overflow-hidden ${
                            currentChatId === chat.id
                              ? "border-2 border-pink-500"
                              : "hover:border-pink-300"
                          }`}
                        >
                          <div className="font-medium truncate w-full overflow-hidden whitespace-nowrap">
                            {chat.title}
                          </div>
                          <div className="text-xs text-gray-500 mt-1 truncate w-full overflow-hidden whitespace-nowrap">
                            {chat.date}
                          </div>
                        </button>

                        {/* Dấu ba chấm (ẩn mặc định, chỉ hiện khi hover vào li) */}
                        <div className="relative">
                          <button
                            onClick={() => toggleOptions(chat.id)}
                            className="ml-2 p-2 rounded-full hover:bg-gray-100 hidden group-hover:block"
                          >
                            <MoreVertical size={20} />
                          </button>

                          {/* Menu sửa & xóa */}
                          {openMenuId === chat.id && (
                            <div className="absolute right-0 mt-2 w-24 bg-white border border-gray-300 rounded-lg shadow-lg z-10">
                              <button
                                onClick={() =>
                                  openEditModal(chat.id, chat.title)
                                }
                                className="flex items-center gap-2 w-full px-3 py-2 hover:bg-gray-100"
                              >
                                <Pencil size={16} /> Sửa
                              </button>
                              <button
                                onClick={() =>
                                  openDeleteModal(
                                    chat.id,
                                    chat.title,
                                    chat.date
                                  )
                                }
                                className="flex items-center gap-2 w-full px-3 py-2 hover:bg-gray-100 border-t"
                              >
                                <Trash2 size={16} /> Xóa
                              </button>
                            </div>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </>
          )}
        </div>

        {/* Chat Area */}
        <div className="flex-grow flex flex-col position: relative ">
          {/* Icon ScrollText ở góc phải trên */}
          <div className="absolute top-20 right-10 z-10">
            <button
              onClick={toggleContextVisibility}
              className="relative group"
              aria-label="Toggle context visibility"
            >
              <ScrollText className="h-6 w-6 text-blue-600" />
              {!showContexts && (
                <div className="absolute top-0 left-0 w-full h-full flex justify-center items-center">
                  <div className="absolute w-full h-1 bg-red-600 transform rotate-45 origin-center" />
                </div>
              )}
              {/* Tooltip */}
              <span className="absolute top-full w-32 left-1/2 transform -translate-x-1/2 mb-4 px-4 py-2 text-sm text-white bg-black rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-300 ease-in-out">
  Ấn để ẩn hiện văn bản pháp luật
</span>

            </button>
          </div>
          <div className="relative flex-grow overflow-y-auto p-6 bg-gradient-to-b from-purple-50 via-pink-50 to-white">
            <div className="max-w-3xl mx-auto">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex mb-8 items-end ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {message.role === "assistant" && (
                    <div className="mr-3">
                      <div className="bg-orange-500 rounded-full p-2">
                        <BotIcon className="h-4 w-4 text-white" />
                      </div>
                    </div>
                  )}
                  <div className="group relative max-w-[80%]">
                    <div
                      className={`relative rounded-2xl p-6 border-2 transition-all duration-300 transform-gpu group-hover:scale-[1.02] group-hover:-translate-y-1 ${
                        message.role === "user"
                          ? "bg-white text-gray-900 border-[#b3e5fc]"
                          : "bg-white text-gray-800 border-orange-300"
                      }`}
                    >
                      <div className="flex items-center mb-3">
                        {message.role === "user" ? (
                          <span className="text-xs opacity-75 flex-grow">
                            {message.timestamp}
                          </span>
                        ) : (
                          <>
                            <span className="font-medium text-orange-700">
                              Trợ lý Pháp luật
                            </span>
                            <span className="text-xs text-gray-500 ml-2">
                              {message.timestamp}
                            </span>
                          </>
                        )}
                      </div>

                      {/* Phần nội dung câu hỏi hoặc phản hồi */}
                      <div className="leading-relaxed space-y-3">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    </div>

                    {/* Hiển thị context ngay dưới botResponse */}
                    {message.role === "assistant" &&
                      message.context &&
                      message.context.length > 0 &&
                      showContexts && (
                        <div className="mt-4 p-4 border-l-4 border-blue-500 bg-blue-50 rounded-md">
                          <h4 className="text-sm font-semibold text-blue-700">
                            📜 Văn bản pháp luật:
                          </h4>
                          <br />
                          {message.context.slice(0, 3).map((law, index) => (
                            <div
                              key={`${message.id}_context_${index}`}
                              className="mt-2"
                            >
                              {law.ten && (
                                <p className="text-sm font-bold text-gray-900">
                                  ⚖️ {law.ten}
                                </p>
                              )}
                              {law.vbqppl && (
                                <p
                                  className="text-xs font-medium max-h-12 overflow-y-auto"
                                  style={{ wordBreak: "break-word" }}
                                >
                                  📌 {law.vbqppl}
                                </p>
                              )}
                              {law.vbqppl_link && (
                                <a
                                  href={law.vbqppl_link}
                                  className="text-sm text-blue-500 hover:underline"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  🔗 Xem chi tiết
                                </a>
                              )}
                              <hr />
                            </div>
                          ))}
                        </div>
                      )}
                  </div>

                  {message.role === "user" && (
                    <div className="ml-3">
                      <div className="bg-[#f5e6d7] rounded-full p-2">
                        <UserIcon className="h-4 w-4 text-gray-700" />
                      </div>
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Area */}
          <div className="border-t border-pink-200 bg-pink-50 p-4">
            <div className="flex items-center justify-center max-w-3xl mx-auto">

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (textareaRef.current) {
                    const trimmedMessage = textareaRef.current.value.trim(); // Loại bỏ khoảng trắng đầu cuối
                    if (trimmedMessage) {
                      handleSendMessage(trimmedMessage);
                      textareaRef.current.value = ""; // Xóa nội dung sau khi gửi
                      textareaRef.current.style.height = "80px"; // Thu nhỏ lại
                    }
                  }
                }}
                className="flex items-center bg-white rounded-xl px-6 py-3 shadow-sm border border-pink-300 flex-grow"
              >
                <textarea
                  ref={textareaRef} // Tham chiếu đến textarea
                  placeholder="Nhập câu hỏi pháp luật của bạn..."
                  className="w-full bg-transparent outline-none text-gray-800 py-3 text-[16px] resize-none h-20 overflow-y-auto"
                  rows={1}
                  style={{ minHeight: "80px", maxHeight: "300px" }}
                  onInput={(e) => {
                    e.currentTarget.style.height = "auto"; // Reset chiều cao
                    e.currentTarget.style.height = `${e.currentTarget.scrollHeight}px`; // Tăng dần theo nội dung
                  }}
                />
                <button
                  type="button"
                  className="p-2 mr-2 bg-pink-100 rounded-lg hover:bg-pink-200 transition"
                  onClick={handleSpeechToText} // Add onClick handler
                >
                  <MicIcon className="h-5 w-5 text-pink-600" />
                </button>
                <button
                  type="submit"
                  className="p-3 bg-pink-500 text-white rounded-lg hover:bg-pink-600"
                >
                  <SendIcon className="h-5 w-5" />
                </button>
              </form>
            </div>
            <p className="text-xs text-pink-500 mt-2 text-center">
              Thông tin được cung cấp chỉ mang tính chất tham khảo và không thay
              thế cho tư vấn pháp lý chuyên nghiệp. ChatBot có thể mắc lỗi, vui
              lòng kiểm tra thông tin quan trọng.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;
