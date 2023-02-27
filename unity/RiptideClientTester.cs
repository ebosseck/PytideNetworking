using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using Riptide;
using Riptide.Transports.Tcp;

public class RiptideClientTester : MonoBehaviour
{
    private Client client;

    private int frameCounter = 0;
    // Start is called before the first frame update


    private const ushort MESSAGE_ID_BOOL = 0;
    private const ushort MESSAGE_ID_BOOL_ARRAY = 1;

    private const ushort MESSAGE_ID_BYTE = 2;
    private const ushort MESSAGE_ID_BYTE_ARRAY = 3;
    private const ushort MESSAGE_ID_SBYTE = 4;
    private const ushort MESSAGE_ID_SBYTE_ARRAY = 5;

    private const ushort MESSAGE_ID_SHORT = 6;
    private const ushort MESSAGE_ID_SHORT_ARRAY = 7;
    private const ushort MESSAGE_ID_USHORT = 8;
    private const ushort MESSAGE_ID_USHORT_ARRAY = 9;

    private const ushort MESSAGE_ID_INT = 10;
    private const ushort MESSAGE_ID_INT_ARRAY = 11;
    private const ushort MESSAGE_ID_UINT = 12;
    private const ushort MESSAGE_ID_UINT_ARRAY = 13;

    private const ushort MESSAGE_ID_LONG = 14;
    private const ushort MESSAGE_ID_LONG_ARRAY = 15;
    private const ushort MESSAGE_ID_ULONG = 16;
    private const ushort MESSAGE_ID_ULONG_ARRAY = 17;

    private const ushort MESSAGE_ID_FLOAT = 18;
    private const ushort MESSAGE_ID_FLOAT_ARRAY = 19;

    private const ushort MESSAGE_ID_DOUBLE = 20;
    private const ushort MESSAGE_ID_DOUBLE_ARRAY = 21;

    private const ushort MESSAGE_ID_STRING = 22;
    private const ushort MESSAGE_ID_STRING_ARRAY = 23;

    private MessageSendMode SendMode = MessageSendMode.Unreliable;
    void Start()
    {
        TcpClient transport = new TcpClient();
        client = new Client(transport);
        client.Connect("127.0.0.1:7777");
    }

    [MessageHandler(MESSAGE_ID_BOOL)]
    private static void handleBool(Message message)
    {
        Debug.Log($"Received Message: {message.GetBool()}");
    }

    [MessageHandler(MESSAGE_ID_BOOL_ARRAY)]
    private static void handleBools(Message message)
    {
        Debug.Log($"Received Message: {message.GetBools()}");
    }
    
    [MessageHandler(MESSAGE_ID_BYTE)]
    private static void handleByte(Message message)
    {
        Debug.Log($"Received Message: {message.GetByte()}");
    }
    
    [MessageHandler(MESSAGE_ID_BYTE_ARRAY)]
    private static void handleBytes(Message message)
    {
        Debug.Log($"Received Message: {message.GetBytes()}");
    }
    
    [MessageHandler(MESSAGE_ID_SBYTE)]
    private static void handleSByte(Message message)
    {
        Debug.Log($"Received Message: {message.GetSByte()}");
    }
    
    [MessageHandler(MESSAGE_ID_SBYTE_ARRAY)]
    private static void handleSBytes(Message message)
    {
        Debug.Log($"Received Message: {message.GetSBytes()}");
    }
    
    [MessageHandler(MESSAGE_ID_SHORT)]
    private static void handleShort(Message message)
    {
        Debug.Log($"Received Message: {message.GetShort()}");
    }
    
    [MessageHandler(MESSAGE_ID_SHORT_ARRAY)]
    private static void handleShorts(Message message)
    {
        Debug.Log($"Received Message: {message.GetShorts()}");
    }
    
    [MessageHandler(MESSAGE_ID_USHORT)]
    private static void handleUShort(Message message)
    {
        Debug.Log($"Received Message: {message.GetUShort()}");
    }
    
    [MessageHandler(MESSAGE_ID_USHORT_ARRAY)]
    private static void handleUShorts(Message message)
    {
        Debug.Log($"Received Message: {message.GetUShorts()}");
    }
    
    [MessageHandler(MESSAGE_ID_INT)]
    private static void handleInt(Message message)
    {
        Debug.Log($"Received Message: {message.GetInt()}");
    }
    
    [MessageHandler(MESSAGE_ID_INT_ARRAY)]
    private static void handleInts(Message message)
    {
        Debug.Log($"Received Message: {message.GetInts()}");
    }
    
    [MessageHandler(MESSAGE_ID_UINT)]
    private static void handleUInt(Message message)
    {
        Debug.Log($"Received Message: {message.GetUInt()}");
    }
    
    [MessageHandler(MESSAGE_ID_UINT_ARRAY)]
    private static void handleUInts(Message message)
    {
        Debug.Log($"Received Message: {message.GetUInts()}");
    }

    [MessageHandler(MESSAGE_ID_LONG)]
    private static void handleLong(Message message)
    {
        Debug.Log($"Received Message: {message.GetLong()}");
    }
    
    [MessageHandler(MESSAGE_ID_LONG_ARRAY)]
    private static void handleLongs(Message message)
    {
        Debug.Log($"Received Message: {message.GetLongs()}");
    }
    
    [MessageHandler(MESSAGE_ID_ULONG)]
    private static void handleULong(Message message)
    {
        Debug.Log($"Received Message: {message.GetULong()}");
    }
    
    [MessageHandler(MESSAGE_ID_ULONG_ARRAY)]
    private static void handleULongs(Message message)
    {
        Debug.Log($"Received Message: {message.GetULongs()}");
    }

    [MessageHandler(MESSAGE_ID_FLOAT)]
    private static void handleFloat(Message message)
    {
        Debug.Log($"Received Message: {message.GetFloat()}");
    }
    
    [MessageHandler(MESSAGE_ID_FLOAT_ARRAY)]
    private static void handleFloats(Message message)
    {
        Debug.Log($"Received Message: {message.GetFloats()}");
    }
    
    [MessageHandler(MESSAGE_ID_DOUBLE)]
    private static void handleDouble(Message message)
    {
        Debug.Log($"Received Message: {message.GetDouble()}");
    }
    
    [MessageHandler(MESSAGE_ID_DOUBLE_ARRAY)]
    private static void handleDoubles(Message message)
    {
        Debug.Log($"Received Message: {message.GetDoubles()}");
    }
    
    [MessageHandler(MESSAGE_ID_STRING)]
    private static void handleString(Message message)
    {
        Debug.Log($"Received Message: {message.GetString()}");
    }
    
    [MessageHandler(MESSAGE_ID_STRING_ARRAY)]
    private static void handleStrings(Message message)
    {
        Debug.Log($"Received Message: {message.GetStrings()}");
    }
    
    // Update is called once per frame
    void FixedUpdate()
    {
        frameCounter += 1;
        client.Update();

        if (frameCounter == 100)
        {
            Message msg = Message.Create(SendMode, MESSAGE_ID_BOOL);
            msg.AddBool(true);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_BOOL_ARRAY);
            msg.AddBools(new[] { true, false, true, false, false, true });
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_BYTE);
            msg.AddByte(42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_BYTE_ARRAY);
            msg.AddBytes(new byte[] { 1, 2, 3, 4, 5, 6});
            client.Send(msg);

            msg = Message.Create(SendMode, MESSAGE_ID_SBYTE);
            msg.AddSByte(-42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_SBYTE_ARRAY);
            msg.AddSBytes(new sbyte[] { -1, 2, -3, 4, -5, 6});
            client.Send(msg);
            
            
            msg = Message.Create(SendMode, MESSAGE_ID_SHORT);
            msg.AddShort(-42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_SHORT_ARRAY);
            msg.AddShorts(new short[] { -1, 2, -3, 4, -5, 6});
            client.Send(msg);

            msg = Message.Create(SendMode, MESSAGE_ID_USHORT);
            msg.AddUShort(42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_USHORT_ARRAY);
            msg.AddUShorts(new ushort[] { 1, 2, 3, 4, 5, 6});
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_INT);
            msg.AddInt(-42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_INT_ARRAY);
            msg.AddInts(new [] { -1, 2, -3, 4, -5, 6});
            client.Send(msg);

            msg = Message.Create(SendMode, MESSAGE_ID_UINT);
            msg.AddUInt(42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_UINT_ARRAY);
            msg.AddUInts(new uint[] { 1, 2, 3, 4, 5, 6});
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_LONG);
            msg.AddLong(-42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_LONG_ARRAY);
            msg.AddLongs(new long[] { -1, 2, -3, 4, -5, 6});
            client.Send(msg);

            msg = Message.Create(SendMode, MESSAGE_ID_ULONG);
            msg.AddULong(42);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_ULONG_ARRAY);
            msg.AddULongs(new ulong[] { 1, 2, 3, 4, 5, 6});
            client.Send(msg);
            
            
            msg = Message.Create(SendMode, MESSAGE_ID_FLOAT);
            msg.AddFloat(3.141f);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_FLOAT_ARRAY);
            msg.AddFloats(new float[] { 1.6f, 2.5f, 3.4f, 4.3f, 5.2f, 6.1f});
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_DOUBLE);
            msg.AddDouble(42.24);
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_DOUBLE_ARRAY);
            msg.AddDoubles(new double[] { 1.6, 2.5, 3.4, 4.3, 5.2, 6.1});
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_STRING);
            msg.AddString("Lorem ipsum in dolor sit amen");
            client.Send(msg);
            
            msg = Message.Create(SendMode, MESSAGE_ID_STRING_ARRAY);
            msg.AddStrings(new string[] { "Lorem ipsum", " in dolor", " sit amen"});
            client.Send(msg);
            
        }

        if (frameCounter == 200)
        {
            Debug.Log("Concluding Test & Disconnecting Client");
            client.Disconnect();
        }
    }
}
