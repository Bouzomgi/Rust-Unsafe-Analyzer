// Declared union field accessing as a field of a struct

fn main() {

	union SomeUnion {
		first: u8
	}

	struct SomeStruct {
		primero: SomeUnion
	}

	let myUnion = SomeUnion{ first: 1 };
	let myStruct = SomeStruct{ primero: myUnion };

	unsafe {
		let a = myStruct.primero.first;
	}
}