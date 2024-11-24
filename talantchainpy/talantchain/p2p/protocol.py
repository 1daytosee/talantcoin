import asyncio
import json
from typing import Any, Dict, Optional, List
from ..core.block import Block
from ..core.transaction import Transaction
from ..crypto.hash import Hash

class Message:
    """P2P message types"""
    HELLO = "hello"
    GET_BLOCKS = "get_blocks"
    BLOCKS = "blocks"
    NEW_BLOCK = "new_block"
    NEW_TRANSACTION = "new_transaction"

class P2PProtocol:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, node: 'Node'):
        self.reader = reader
        self.writer = writer
        self.node = node
        self.addr = writer.get_extra_info('peername')
    
    async def handle(self):
        """Handle incoming connection"""
        try:
            while True:
                data = await self.reader.readline()
                if not data:
                    break
                    
                message = json.loads(data.decode())
                await self.handle_message(message)
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            self.writer.close()
            await self.writer.wait_closed()
    
    async def handle_message(self, message: Dict[str, Any]):
        """Handle a single message"""
        msg_type = message.get('type')
        payload = message.get('payload')
        
        if msg_type == 'block':
            await self.handle_block(payload)
        elif msg_type == 'transaction':
            await self.handle_transaction(payload)
        elif msg_type == 'get_blocks':
            await self.handle_get_blocks(payload)
        elif msg_type == 'blocks':
            await self.handle_blocks(payload)
        elif msg_type == Message.HELLO:
            await self._handle_hello(payload)
        elif msg_type == Message.GET_BLOCKS:
            await self._handle_get_blocks(payload)
        elif msg_type == Message.BLOCKS:
            await self._handle_blocks(payload)
        elif msg_type == Message.NEW_BLOCK:
            await self._handle_new_block(payload)
        elif msg_type == Message.NEW_TRANSACTION:
            await self._handle_new_transaction(payload)
    
    async def send_message(self, msg_type: str, payload: Any):
        """Send a message to peer"""
        message = json.dumps({
            'type': msg_type,
            'payload': payload
        }).encode() + b'\n'
        self.writer.write(message)
        await self.writer.drain()
    
    async def send_block(self, block: Block):
        """Send a block to peer"""
        await self.send_message('block', {
            'hash': block.hash.hex(),
            'header': {
                'version': block.header.version,
                'prev_hash': block.header.prev_hash.hex(),
                'merkle_root': block.header.merkle_root.hex(),
                'timestamp': block.header.timestamp,
                'difficulty': block.header.difficulty,
                'nonce': block.header.nonce
            },
            'transactions': [tx.to_dict() for tx in block.transactions]
        })
    
    async def send_transaction(self, tx: Transaction):
        """Send a transaction to peer"""
        await self.send_message('transaction', tx.to_dict())
    
    async def handle_block(self, payload: Dict):
        """Handle received block"""
        try:
            # Convert payload back to Block object
            block = Block.from_dict(payload)
            
            # Verify and add to blockchain
            if self.node.blockchain.add_block(block):
                # Broadcast to other peers
                await self.node.broadcast_block(block)
        except Exception as e:
            print(f"Error handling block: {e}")
    
    async def handle_transaction(self, payload: Dict):
        """Handle received transaction"""
        try:
            # Convert payload back to Transaction object
            tx = Transaction.from_dict(payload)
            
            # Verify and add to mempool
            if self.node.add_transaction(tx):
                # Broadcast to other peers
                await self.node.broadcast_transaction(tx)
        except Exception as e:
            print(f"Error handling transaction: {e}")
    
    async def handle_get_blocks(self, payload: Dict):
        """Handle get_blocks request"""
        try:
            start_height = payload.get('start_height', 0)
            end_height = payload.get('end_height')
            
            # Get requested blocks
            blocks = self.node.blockchain.get_blocks(start_height, end_height)
            
            # Send blocks
            await self.send_message('blocks', [
                block.to_dict() for block in blocks
            ])
        except Exception as e:
            print(f"Error handling get_blocks: {e}")
    
    async def handle_blocks(self, payload: List[Dict]):
        """Handle received blocks"""
        try:
            for block_dict in payload:
                block = Block.from_dict(block_dict)
                self.node.blockchain.add_block(block)
        except Exception as e:
            print(f"Error handling blocks: {e}")
    
    async def _handle_hello(self, payload: Dict[str, Any]):
        """Handle hello message"""
        self.peer_info = payload
        await self._send_message(Message.HELLO, {
            'version': 1,
            'height': len(self.node.blockchain.chain)
        })
    
    async def _handle_get_blocks(self, payload: Dict[str, Any]):
        """Handle get_blocks message"""
        start_height = payload.get('start_height', 0)
        end_height = payload.get('end_height', len(self.node.blockchain.chain))
        
        blocks = self.node.blockchain.chain[start_height:end_height]
        blocks_data = [self._serialize_block(block) for block in blocks]
        
        await self._send_message(Message.BLOCKS, {
            'blocks': blocks_data
        })
    
    async def _handle_blocks(self, payload: Dict[str, Any]):
        """Handle blocks message"""
        blocks_data = payload.get('blocks', [])
        for block_data in blocks_data:
            block = self._deserialize_block(block_data)
            self.node.blockchain.add_block(block)
    
    async def _handle_new_block(self, payload: Dict[str, Any]):
        """Handle new_block message"""
        block = self._deserialize_block(payload)
        if self.node.blockchain.add_block(block):
            # Propagate to other peers
            await self.node.broadcast_block(block, exclude=self)
    
    async def _handle_new_transaction(self, payload: Dict[str, Any]):
        """Handle new_transaction message"""
        tx = self._deserialize_transaction(payload)
        if self.node.blockchain.add_transaction(tx):
            # Propagate to other peers
            await self.node.broadcast_transaction(tx, exclude=self)
    
    def _serialize_block(self, block: Block) -> Dict[str, Any]:
        """Serialize block to JSON-compatible format"""
        return {
            'header': {
                'version': block.header.version,
                'prev_hash': str(block.header.prev_hash),
                'merkle_root': str(block.header.merkle_root),
                'timestamp': block.header.timestamp,
                'difficulty': block.header.difficulty,
                'nonce': block.header.nonce
            },
            'transactions': [self._serialize_transaction(tx) for tx in block.transactions]
        }
    
    def _deserialize_block(self, data: Dict[str, Any]) -> Block:
        """Deserialize block from JSON-compatible format"""
        header_data = data['header']
        header = BlockHeader(
            version=header_data['version'],
            prev_hash=Hash.from_string(header_data['prev_hash']),
            merkle_root=Hash.from_string(header_data['merkle_root']),
            timestamp=header_data['timestamp'],
            difficulty=header_data['difficulty'],
            nonce=header_data['nonce']
        )
        transactions = [self._deserialize_transaction(tx_data) 
                       for tx_data in data['transactions']]
        return Block(header=header, transactions=transactions)
    
    def _serialize_transaction(self, tx: Transaction) -> Dict[str, Any]:
        """Serialize transaction to JSON-compatible format"""
        return {
            'version': tx.version,
            'inputs': [{
                'prev_tx': str(input.prev_tx),
                'index': input.index,
                'signature': input.signature.hex() if input.signature else None
            } for input in tx.inputs],
            'outputs': [{
                'amount': output.amount,
                'public_key': output.public_key.hex()
            } for output in tx.outputs],
            'lock_time': tx.lock_time
        }
    
    def _deserialize_transaction(self, data: Dict[str, Any]) -> Transaction:
        """Deserialize transaction from JSON-compatible format"""
        inputs = [TxInput(
            prev_tx=Hash.from_string(input['prev_tx']),
            index=input['index'],
            signature=bytes.fromhex(input['signature']) if input['signature'] else None
        ) for input in data['inputs']]
        
        outputs = [TxOutput(
            amount=output['amount'],
            public_key=bytes.fromhex(output['public_key'])
        ) for output in data['outputs']]
        
        return Transaction(
            version=data['version'],
            inputs=inputs,
            outputs=outputs,
            lock_time=data['lock_time']
        )
    
    async def _send_message(self, msg_type: str, payload: Dict[str, Any]):
        """Send message to peer"""
        message = {
            'type': msg_type,
            'payload': payload
        }
        data = json.dumps(message).encode()
        self.writer.write(data)
        await self.writer.drain()
