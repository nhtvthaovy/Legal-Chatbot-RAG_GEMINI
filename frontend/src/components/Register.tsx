import React, { useState } from "react";
import { FcGoogle } from "react-icons/fc";
import axios from "axios"; // Thêm axios để gọi API

const Register = () => {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!name) {
      setError("Tên không được để trống!");
      return;
    }

    if (password !== confirmPassword) {
      setError("Mật khẩu không khớp!");
      return;
    }

    try {
      const response = await axios.post(
        "http://localhost:5000/api/v1/auth/register",
        {
          name, // Gửi tên lên API
          email,
          password,
        }
      );
      setSuccess(response.data.message);
    } catch (err: any) {
      setError(err.response?.data?.error || "Đã xảy ra lỗi!");
    }
  };

  return (
    <div className="flex items-center justify-center h-screen ">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-sm w-full">
        <h2 className="text-2xl font-bold text-center text-gray-700 mb-6">
          Đăng ký
        </h2>
        <div>
          {[...Array(40)].map((_, i) => (
            <div
              key={i}
              className="absolute rounded-full mix-blend-multiply animate-float"
              style={{
                width: `${Math.random() * 50 + 20}px`, // Kích thước nhỏ hơn
                height: `${Math.random() * 50 + 20}px`,
                backgroundColor: `hsl(${Math.random() * 360}, 70%, 90%)`, // Màu sáng hơn
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                opacity: 0.6, // Làm mềm hiệu ứng
                animation: `float ${
                  Math.random() * 2 + 4
                }s infinite ease-in-out`, // Điều chỉnh thời gian float
              }}
            ></div>
          ))}
        </div>

        {error && (
          <p className="text-red-500 text-sm text-center mb-4">{error}</p>
        )}
        {success && (
          <p className="text-green-500 text-sm text-center mb-4">{success}</p>
        )}
        <form onSubmit={handleRegister} className="space-y-4">
          <input
            type="text"
            placeholder="Tên"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-400"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-400"
            required
          />
          <input
            type="password"
            placeholder="Mật khẩu"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-400"
            required
          />
          <input
            type="password"
            placeholder="Xác nhận mật khẩu"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-400"
            required
          />
          <button
            type="submit"
            className="w-full p-3 bg-orange-300 text-white rounded-lg hover:bg-orange-400 transition-all"
          >
            Đăng Ký
          </button>
        </form>
        {/* <div className="mt-4 flex items-center justify-center">
          <button className="flex items-center gap-2 border border-gray-300 p-3 rounded-lg w-full hover:bg-gray-100 transition-all">
            <FcGoogle className="text-2xl" />
            <span className="text-gray-700">Đăng ký với Google</span>
          </button>
        </div> */}
        <p className="text-center text-sm text-gray-600 mt-4">
          Đã có tài khoản?{" "}
          <a href="/login" className="text-blue-500 hover:underline">
            Đăng nhập
          </a>
        </p>
      </div>
    </div>
  );
};

export default Register;
