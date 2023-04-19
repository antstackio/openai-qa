import React, { useEffect, useState } from 'react'
import "./App.css"
import {AiOutlineSend} from 'react-icons/ai'
import axios from 'axios'

const App = () => {
  const [ question, setQuestion ] = useState('')
  const [ btnActive, setBtnActive ] = useState(false)
  const [ allResponse, setAllResponse ] = useState([])

  const handleSubmit = async () =>{
    setBtnActive(true)
    const allRes = {
      text: question,
      type: "question"
    }
    setAllResponse((prev) => [...prev,allRes])
    setQuestion('')
    const data = {
      prompt: question
    }

    try {
      const response = await axios.post('https://API.execute-api.REGION.amazonaws.com/STAGE/PATH',data)
      setBtnActive(false)
      const formattedResponse = {
        text: response.data.response,
        type: "answer"
      }
      setAllResponse(prevResponse => [...prevResponse,formattedResponse])
    } catch (error) {
      console.log('error',error)
      setBtnActive(false)
    }
  }

  useEffect(() =>{
    const chatWindow = document.getElementById('msg');
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }, [allResponse.length])

  return(
    <div className="bot-app">
      <div className='initial-message'>
        <p className='logo'>A</p>
        <p className='message'>Hello &#x1F44B; I am a chat bot, here to help you to know about Antstack &#x2764;&#xFE0F;</p>
      </div>
      <div className='msg-dialogue' id = 'msg'>
        {
          allResponse.map((res, idx) =>{
            return <div key={idx}  className={res.type === 'question'? 'right':'left'}>{res.text}</div>
          })
        }
      </div>
      <div className='input-question'>
        <input className='question-input' type='text' value={question} onChange={(e) => setQuestion(e.target.value)} placeholder='Ask Me anything...' />
        <button onClick={handleSubmit} disabled={btnActive}><AiOutlineSend/></button>
      </div>
    </div>
  )
};

export default App